import sqlite3
from datetime import datetime, timezone
from uuid import UUID

import pytest

import app.reservas as reservas
from app.database import connect, initialize_database
from app.disponibilidad import EquipoNoEncontradoError, consultar_disponibilidad
from app.reservas import (
    ReservaNoEncontradaError,
    ReservaSuperpuestaError,
    ReservaYaCanceladaError,
    SolicitanteInvalidoError,
    cancelar_reserva,
    crear_reserva,
)


AHORA = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
INTERVALO = ("2026-01-10", "10:00", "2026-01-10", "11:00")


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "reservas.sqlite3"
    initialize_database(path)
    return path


def crear(database_path, equipo_id="MIC-01", solicitante="Investigación", intervalo=INTERVALO):
    return crear_reserva(
        equipo_id,
        solicitante,
        *intervalo,
        database_path=database_path,
        ahora=AHORA,
    )


def obtener_reservas(database_path):
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM reservas ORDER BY id"
        ).fetchall()


def test_crear_reserva_valida_y_genera_uuid(database_path):
    reservation_id = crear(database_path)

    assert str(UUID(reservation_id)) == reservation_id
    row = obtener_reservas(database_path)[0]
    assert row["id"] == reservation_id
    assert row["equipo_id"] == "MIC-01"
    assert row["solicitante"] == "Investigación"
    assert row["inicio_utc"] == "2026-01-10T13:00:00+00:00"
    assert row["fin_utc"] == "2026-01-10T14:00:00+00:00"
    assert row["estado"] == "activa"
    assert row["creada_utc"] == "2026-01-01T00:00:00+00:00"
    assert row["cancelada_utc"] is None


@pytest.mark.parametrize("solicitante", ["", "   ", "\t\n"])
def test_rechazar_solicitante_vacio_o_solo_espacios(database_path, solicitante):
    with pytest.raises(SolicitanteInvalidoError):
        crear(database_path, solicitante=solicitante)

    assert obtener_reservas(database_path) == []


def test_rechazar_equipo_inexistente_sin_dejar_registro(database_path):
    with pytest.raises(EquipoNoEncontradoError, match="NO-EXISTE"):
        crear(database_path, equipo_id="NO-EXISTE")

    assert obtener_reservas(database_path) == []


def test_rechazar_superposicion_sin_insertar_reserva_parcial(database_path):
    crear(database_path)

    with pytest.raises(ReservaSuperpuestaError):
        crear(database_path, intervalo=("2026-01-10", "10:30", "2026-01-10", "11:30"))

    assert len(obtener_reservas(database_path)) == 1


def test_permitir_reservas_consecutivas(database_path):
    crear(database_path)

    second_id = crear(
        database_path,
        intervalo=("2026-01-10", "11:00", "2026-01-10", "12:00"),
    )

    assert len(obtener_reservas(database_path)) == 2
    assert any(row["id"] == second_id for row in obtener_reservas(database_path))


def test_permitir_reservas_simultaneas_en_equipos_diferentes(database_path):
    crear(database_path, equipo_id="MIC-01")

    second_id = crear(database_path, equipo_id="MIC-02")

    assert len(obtener_reservas(database_path)) == 2
    assert any(row["id"] == second_id for row in obtener_reservas(database_path))


def test_cancelar_conserva_datos_originales_y_registra_instante_utc(database_path):
    reservation_id = crear(database_path)
    original = obtener_reservas(database_path)[0]

    cancelar_reserva(reservation_id, database_path=database_path, ahora=AHORA)

    cancelled = obtener_reservas(database_path)[0]
    for field in ("id", "equipo_id", "solicitante", "inicio_utc", "fin_utc", "creada_utc"):
        assert cancelled[field] == original[field]
    assert cancelled["estado"] == "cancelada"
    assert cancelled["cancelada_utc"] == "2026-01-01T00:00:00+00:00"


def test_cancelar_libera_intervalo(database_path):
    reservation_id = crear(database_path)

    cancelar_reserva(reservation_id, database_path=database_path, ahora=AHORA)
    result = consultar_disponibilidad(
        "MIC-01", *INTERVALO, database_path=database_path, ahora=AHORA
    )

    assert result.disponible is True


def test_rechazar_segunda_cancelacion_sin_modificar_registro(database_path):
    reservation_id = crear(database_path)
    cancelar_reserva(reservation_id, database_path=database_path, ahora=AHORA)
    before_retry = obtener_reservas(database_path)[0]

    with pytest.raises(ReservaYaCanceladaError):
        cancelar_reserva(reservation_id, database_path=database_path, ahora=AHORA)

    after_retry = obtener_reservas(database_path)[0]
    assert tuple(after_retry) == tuple(before_retry)


def test_rechazar_cancelacion_de_reserva_inexistente(database_path):
    with pytest.raises(ReservaNoEncontradaError):
        cancelar_reserva("no-existe", database_path=database_path, ahora=AHORA)

    assert obtener_reservas(database_path) == []


def test_transaccion_inmediata_cubre_busqueda_e_insercion(database_path, monkeypatch):
    statements = []
    connection = connect(database_path)
    connection.set_trace_callback(statements.append)
    monkeypatch.setattr(reservas, "connect", lambda _: connection)

    crear(database_path)

    normalized_statements = [statement.upper() for statement in statements]
    begin_index = normalized_statements.index("BEGIN IMMEDIATE")
    select_index = next(
        index
        for index, statement in enumerate(normalized_statements)
        if statement.strip().startswith("SELECT ID") and "FROM RESERVAS" in statement
    )
    insert_index = next(
        index
        for index, statement in enumerate(normalized_statements)
        if statement.strip().startswith("INSERT INTO RESERVAS")
    )
    assert begin_index < select_index < insert_index


def test_error_de_sqlite_hace_rollback_sin_registro_parcial(database_path, monkeypatch):
    original_connect = reservas.connect

    def connect_with_failing_trigger(path):
        connection = original_connect(path)
        connection.execute(
            """
            CREATE TEMP TRIGGER fail_reserva_insert
            BEFORE INSERT ON reservas
            BEGIN
                SELECT RAISE(ABORT, 'fallo simulado al insertar');
            END;
            """
        )
        return connection

    monkeypatch.setattr(reservas, "connect", connect_with_failing_trigger)

    with pytest.raises(sqlite3.IntegrityError, match="fallo simulado"):
        crear(database_path)

    assert obtener_reservas(database_path) == []