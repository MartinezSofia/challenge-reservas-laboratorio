from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.database import DEFAULT_DATABASE_PATH, connect
from app.validaciones import IntervaloUTC, validar_intervalo


class EquipoNoEncontradoError(LookupError):
    """Indica que el identificador de equipo no existe en el inventario."""


@dataclass(frozen=True)
class ResultadoDisponibilidad:
    equipo_id: str
    disponible: bool
    reserva_conflictiva_id: str | None = None


def consultar_disponibilidad(
    equipo_id: str,
    fecha_inicio: str,
    hora_inicio: str,
    fecha_fin: str,
    hora_fin: str,
    *,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    ahora: datetime | None = None,
) -> ResultadoDisponibilidad:
    intervalo: IntervaloUTC = validar_intervalo(
        fecha_inicio,
        hora_inicio,
        fecha_fin,
        hora_fin,
        ahora=ahora,
    )
    connection = connect(database_path)
    try:
        equipment = connection.execute(
            "SELECT 1 FROM equipos WHERE id = ?", (equipo_id,)
        ).fetchone()
        if equipment is None:
            raise EquipoNoEncontradoError(f"El equipo {equipo_id} no existe.")

        conflict = connection.execute(
            """
            SELECT id
            FROM reservas
            WHERE equipo_id = ?
              AND estado = 'activa'
              AND inicio_utc < ?
              AND fin_utc > ?
            LIMIT 1
            """,
            (equipo_id, intervalo.fin_utc, intervalo.inicio_utc),
        ).fetchone()
        if conflict is not None:
            return ResultadoDisponibilidad(
                equipo_id=equipo_id,
                disponible=False,
                reserva_conflictiva_id=conflict["id"],
            )
        return ResultadoDisponibilidad(equipo_id=equipo_id, disponible=True)
    finally:
        connection.close()