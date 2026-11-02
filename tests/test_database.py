import sqlite3
from uuid import uuid4

from app.database import connect, initialize_database


def test_initialize_creates_schema_and_exact_inventory(tmp_path):
    database_path = tmp_path / "reservas.sqlite3"

    initialize_database(database_path)

    with connect(database_path) as connection:
        equipment = connection.execute(
            "SELECT id, nombre FROM equipos ORDER BY id"
        ).fetchall()
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert [(row["id"], row["nombre"]) for row in equipment] == [
        ("FUE-01", "Fuente de alimentación"),
        ("MIC-01", "Microscopio digital"),
        ("MIC-02", "Microscopio digital"),
        ("MUL-01", "Multímetro"),
        ("OSC-01", "Osciloscopio"),
    ]
    assert {"equipos", "reservas"}.issubset(table_names)


def test_connection_enables_foreign_keys(tmp_path):
    connection = connect(tmp_path / "reservas.sqlite3")
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()


def test_reinitializing_preserves_existing_reservations(tmp_path):
    database_path = tmp_path / "reservas.sqlite3"
    initialize_database(database_path)
    reservation_id = str(uuid4())
    created_at = "2026-01-01T12:00:00+00:00"

    with connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO reservas (
                id, equipo_id, solicitante, inicio_utc, fin_utc,
                estado, creada_utc, cancelada_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                reservation_id,
                "MIC-01",
                "Prueba",
                "2030-01-01T10:00:00+00:00",
                "2030-01-01T11:00:00+00:00",
                "activa",
                created_at,
            ),
        )

    initialize_database(database_path)

    with connect(database_path) as connection:
        reservation = connection.execute(
            "SELECT id, estado FROM reservas WHERE id = ?", (reservation_id,)
        ).fetchone()
        equipment_count = connection.execute(
            "SELECT COUNT(*) FROM equipos"
        ).fetchone()[0]

    assert tuple(reservation) == (reservation_id, "activa")
    assert equipment_count == 5


def test_reservations_require_an_existing_equipment(tmp_path):
    database_path = tmp_path / "reservas.sqlite3"
    initialize_database(database_path)

    with connect(database_path) as connection:
        try:
            connection.execute(
                """
                INSERT INTO reservas (
                    id, equipo_id, solicitante, inicio_utc, fin_utc,
                    estado, creada_utc, cancelada_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    str(uuid4()),
                    "NO-EXISTE",
                    "Prueba",
                    "2030-01-01T10:00:00+00:00",
                    "2030-01-01T11:00:00+00:00",
                    "activa",
                    "2026-01-01T12:00:00+00:00",
                ),
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Se aceptó una reserva para un equipo inexistente.")