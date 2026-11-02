from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.database import connect, initialize_database
from app.disponibilidad import (
    EquipoNoEncontradoError,
    consultar_disponibilidad,
)
from app.validaciones import ValidacionTemporalError


AHORA = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
INTERVALO_CONSULTA = ("2026-01-10", "10:00", "2026-01-10", "11:00")


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "reservas.sqlite3"
    initialize_database(path)
    return path


def insertar_reserva(
    database_path,
    equipo_id,
    inicio_utc,
    fin_utc,
    *,
    estado="activa",
):
    reservation_id = str(uuid4())
    with connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO reservas (
                id, equipo_id, solicitante, inicio_utc, fin_utc,
                estado, creada_utc, cancelada_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reservation_id,
                equipo_id,
                "Prueba",
                inicio_utc,
                fin_utc,
                estado,
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00" if estado == "cancelada" else None,
            ),
        )
    return reservation_id


def consultar(database_path, equipo_id="MIC-01", intervalo=INTERVALO_CONSULTA):
    return consultar_disponibilidad(
        equipo_id,
        *intervalo,
        database_path=database_path,
        ahora=AHORA,
    )


def test_equipo_inexistente_se_distingue_claramente(database_path):
    with pytest.raises(EquipoNoEncontradoError, match="NO-EXISTE"):
        consultar(database_path, "NO-EXISTE")


def test_intervalo_invalido_se_distingue_claramente(database_path):
    invalid_interval = ("2026-01-10", "11:00", "2026-01-10", "10:00")

    with pytest.raises(ValidacionTemporalError):
        consultar(database_path, intervalo=invalid_interval)


def test_intervalo_sin_superposicion_indica_disponible(database_path):
    result = consultar(database_path)

    assert result.equipo_id == "MIC-01"
    assert result.disponible is True
    assert result.reserva_conflictiva_id is None


def test_superposicion_con_reserva_activa_indica_equipo_ocupado(database_path):
    reservation_id = insertar_reserva(
        database_path,
        "MIC-01",
        "2026-01-10T13:30:00+00:00",
        "2026-01-10T14:30:00+00:00",
    )

    result = consultar(database_path)

    assert result.disponible is False
    assert result.reserva_conflictiva_id == reservation_id


@pytest.mark.parametrize(
    ("existing_start", "existing_end"),
    [
        ("2026-01-10T12:00:00+00:00", "2026-01-10T13:00:00+00:00"),
        ("2026-01-10T14:00:00+00:00", "2026-01-10T15:00:00+00:00"),
    ],
)
def test_intervalos_consecutivos_estan_disponibles(
    database_path, existing_start, existing_end
):
    insertar_reserva(database_path, "MIC-01", existing_start, existing_end)

    assert consultar(database_path).disponible is True


def test_reserva_simultanea_de_otro_equipo_no_bloquea(database_path):
    insertar_reserva(
        database_path,
        "MIC-02",
        "2026-01-10T13:30:00+00:00",
        "2026-01-10T14:30:00+00:00",
    )

    assert consultar(database_path, "MIC-01").disponible is True


def test_reserva_cancelada_no_bloquea_disponibilidad(database_path):
    insertar_reserva(
        database_path,
        "MIC-01",
        "2026-01-10T13:30:00+00:00",
        "2026-01-10T14:30:00+00:00",
        estado="cancelada",
    )

    assert consultar(database_path).disponible is True