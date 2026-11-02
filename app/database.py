import json
import sqlite3
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "reservas.sqlite3"
DEFAULT_INVENTORY_PATH = PROJECT_ROOT / "data" / "inventario.json"


def connect(database_path: str | Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    path = str(database_path)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _load_inventory(inventory_path: str | Path) -> list[dict[str, str]]:
    with Path(inventory_path).open(encoding="utf-8") as inventory_file:
        inventory: Any = json.load(inventory_file)

    if not isinstance(inventory, list):
        raise ValueError("El inventario debe ser una lista de equipos.")

    expected_inventory = {
        "MIC-01": "Microscopio digital",
        "MIC-02": "Microscopio digital",
        "OSC-01": "Osciloscopio",
        "MUL-01": "Multímetro",
        "FUE-01": "Fuente de alimentación",
    }
    loaded_inventory: dict[str, str] = {}
    for item in inventory:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not isinstance(item.get("nombre"), str)
        ):
            raise ValueError("Cada equipo debe tener campos de texto 'id' y 'nombre'.")
        if item["id"] in loaded_inventory:
            raise ValueError(f"El identificador de equipo {item['id']} está duplicado.")
        loaded_inventory[item["id"]] = item["nombre"]

    if loaded_inventory != expected_inventory:
        raise ValueError("El inventario debe contener exactamente las cinco unidades definidas.")

    return inventory


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    inventory_path: str | Path = DEFAULT_INVENTORY_PATH,
) -> None:
    inventory = _load_inventory(inventory_path)
    connection = connect(database_path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS equipos (
                id TEXT PRIMARY KEY CHECK (
                    id IN ('MIC-01', 'MIC-02', 'OSC-01', 'MUL-01', 'FUE-01')
                ),
                nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0)
            );

            CREATE TABLE IF NOT EXISTS reservas (
                id TEXT PRIMARY KEY,
                equipo_id TEXT NOT NULL,
                solicitante TEXT NOT NULL CHECK (length(trim(solicitante)) > 0),
                inicio_utc TEXT NOT NULL,
                fin_utc TEXT NOT NULL,
                estado TEXT NOT NULL CHECK (estado IN ('activa', 'cancelada')),
                creada_utc TEXT NOT NULL,
                cancelada_utc TEXT,
                CHECK (inicio_utc < fin_utc),
                CHECK (
                    (estado = 'activa' AND cancelada_utc IS NULL)
                    OR (estado = 'cancelada' AND cancelada_utc IS NOT NULL)
                ),
                FOREIGN KEY (equipo_id) REFERENCES equipos(id)
            );

            CREATE INDEX IF NOT EXISTS idx_reservas_equipo_estado_intervalo
            ON reservas (equipo_id, estado, inicio_utc, fin_utc);
            """
        )
        with connection:
            connection.executemany(
                """
                INSERT INTO equipos (id, nombre)
                VALUES (:id, :nombre)
                ON CONFLICT(id) DO UPDATE SET nombre = excluded.nombre
                """,
                inventory,
            )
    finally:
        connection.close()