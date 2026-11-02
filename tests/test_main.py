from datetime import datetime, timezone

import pytest

from app.database import connect, initialize_database
from app.main import run
from app.reservas import crear_reserva


AHORA = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
INTERVALO = ("2090-01-10", "10:00", "2090-01-10", "11:00")


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "reservas.sqlite3"


def ejecutar(database_path, respuestas):
    outputs = []
    inputs = iter(respuestas)
    run(
        database_path=database_path,
        input_fn=lambda _prompt: next(inputs),
        output_fn=outputs.append,
    )
    return outputs


def sembrar_reserva(database_path, intervalo=INTERVALO):
    initialize_database(database_path)
    return crear_reserva(
        "MIC-01",
        "Prueba de consola",
        *intervalo,
        database_path=database_path,
        ahora=AHORA,
    )


def test_arranque_inicializa_base_temporal_y_permite_salir(database_path):
    outputs = ejecutar(database_path, ["0"])

    assert any("Saliendo del sistema" in output for output in outputs)
    with connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM equipos").fetchone()[0] == 5


def test_opcion_invalida_vuelve_al_menu(database_path):
    outputs = ejecutar(database_path, ["9", "0"])

    assert any("Opción inválida" in output for output in outputs)
    assert sum("Sistema de reservas" in output for output in outputs) == 2


def test_consultar_disponibilidad_muestra_equipo_disponible(database_path):
    outputs = ejecutar(
        database_path,
        ["1", "MIC-01", "2090-01-10", "10:00", "2090-01-10", "11:00", "0"],
    )

    assert any("MIC-01 está disponible" in output for output in outputs)


def test_consultar_disponibilidad_muestra_equipo_ocupado(database_path):
    reservation_id = sembrar_reserva(database_path)
    outputs = ejecutar(
        database_path,
        ["1", "MIC-01", *INTERVALO, "0"],
    )

    assert any("está ocupado" in output and reservation_id in output for output in outputs)


def test_consulta_muestra_error_de_equipo_inexistente(database_path):
    outputs = ejecutar(
        database_path,
        ["1", "NO-EXISTE", *INTERVALO, "0"],
    )

    assert any("Error:" in output and "NO-EXISTE" in output for output in outputs)


@pytest.mark.parametrize(
    ("intervalo", "expected_message"),
    [
        pytest.param(
            ("10-01-2090", "10:00", "2090-01-10", "11:00"),
            "formato AAAA-MM-DD",
            id="fecha-invalida",
        ),
        pytest.param(
            ("2090-01-10", "25:00", "2090-01-10", "11:00"),
            "hora no es válida",
            id="hora-invalida",
        ),
    ],
)
def test_consulta_muestra_error_de_fecha_u_hora_invalida(
    database_path, intervalo, expected_message
):
    outputs = ejecutar(database_path, ["1", "MIC-01", *intervalo, "0"])

    assert any(
        output.startswith("Error:") and expected_message in output
        for output in outputs
    )


def test_crear_reserva_desde_consola_permite_cruzar_medianoche(database_path):
    intervalo = ("2090-12-31", "23:00", "2091-01-01", "01:00")
    outputs = ejecutar(
        database_path,
        ["2", "MIC-01", "Solicitante", *intervalo, "0"],
    )

    success = next(output for output in outputs if "Reserva creada correctamente" in output)
    reservation_id = success.rsplit(" ", 1)[-1]
    with connect(database_path) as connection:
        reservation = connection.execute(
            "SELECT inicio_utc, fin_utc FROM reservas WHERE id = ?", (reservation_id,)
        ).fetchone()

    assert tuple(reservation) == (
        "2091-01-01T02:00:00+00:00",
        "2091-01-01T04:00:00+00:00",
    )


@pytest.mark.parametrize(
    ("solicitante", "intervalo", "expected_message"),
    [
        pytest.param("   ", INTERVALO, "solicitante", id="solicitante-solo-espacios"),
        pytest.param(
            "Investigación",
            ("10-01-2090", "10:00", "2090-01-10", "11:00"),
            "formato aaaa-mm-dd",
            id="fecha-de-inicio-invalida",
        ),
    ],
)
def test_crear_muestra_errores_de_entrada_sin_salir_del_menu(
    database_path, solicitante, intervalo, expected_message
):
    outputs = ejecutar(
        database_path,
        ["2", "MIC-01", solicitante, *intervalo, "0"],
    )

    assert any("Error:" in output and expected_message in output.lower() for output in outputs)
    with connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM reservas").fetchone()[0] == 0


def test_crear_muestra_equipo_inexistente_y_superposicion(database_path):
    sembrar_reserva(database_path)
    outputs = ejecutar(
        database_path,
        [
            "2", "NO-EXISTE", "Solicitante", *INTERVALO,
            "2", "MIC-01", "Solicitante", *INTERVALO,
            "0",
        ],
    )

    errors = [output for output in outputs if output.startswith("Error:")]
    assert any("NO-EXISTE" in output for output in errors)
    assert any("superpone" in output for output in errors)


def test_cancelar_muestra_exito_inexistente_y_ya_cancelada(database_path):
    reservation_id = sembrar_reserva(database_path)
    outputs = ejecutar(
        database_path,
        ["3", reservation_id, "3", reservation_id, "3", "no-existe", "0"],
    )

    assert any("cancelada correctamente" in output for output in outputs)
    assert any("ya está cancelada" in output for output in outputs)
    assert any("no existe" in output for output in outputs)


def test_cancelar_conserva_datos_y_libera_intervalo_para_nueva_reserva(database_path):
    reservation_id = sembrar_reserva(database_path)
    with connect(database_path) as connection:
        original = connection.execute(
            "SELECT * FROM reservas WHERE id = ?", (reservation_id,)
        ).fetchone()

    outputs = ejecutar(
        database_path,
        [
            "3", reservation_id,
            "2", "MIC-01", "Nueva solicitante", *INTERVALO,
            "0",
        ],
    )

    assert any("cancelada correctamente" in output for output in outputs)
    assert any("Reserva creada correctamente" in output for output in outputs)
    with connect(database_path) as connection:
        cancelled = connection.execute(
            "SELECT * FROM reservas WHERE id = ?", (reservation_id,)
        ).fetchone()
        active = connection.execute(
            "SELECT * FROM reservas WHERE equipo_id = ? AND estado = 'activa'",
            ("MIC-01",),
        ).fetchone()

    for field in ("id", "equipo_id", "solicitante", "inicio_utc", "fin_utc", "creada_utc"):
        assert cancelled[field] == original[field]
    assert cancelled["estado"] == "cancelada"
    assert cancelled["cancelada_utc"] is not None
    assert active["solicitante"] == "Nueva solicitante"
    assert active["inicio_utc"] == original["inicio_utc"]
    assert active["fin_utc"] == original["fin_utc"]


def test_eof_durante_operacion_sale_sin_traceback(database_path):
    responses = iter(["1", "MIC-01"])
    outputs = []

    def input_with_eof(_prompt):
        try:
            return next(responses)
        except StopIteration:
            raise EOFError from None

    run(
        database_path=database_path,
        input_fn=input_with_eof,
        output_fn=outputs.append,
    )

    assert any("Entrada finalizada. Saliendo del sistema." in output for output in outputs)