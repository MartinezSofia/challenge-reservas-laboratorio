import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.database import DEFAULT_DATABASE_PATH, connect
from app.disponibilidad import (
    EquipoNoEncontradoError,
    buscar_reserva_conflictiva,
)
from app.validaciones import (
    FORMATO_UTC,
    IntervaloUTC,
    ValidacionTemporalError,
    validar_intervalo,
)


class SolicitanteInvalidoError(ValueError):
    """Indica que el solicitante está vacío o contiene solo espacios."""


class ReservaSuperpuestaError(ValueError):
    """Indica que otra reserva activa ocupa parte del intervalo solicitado."""

    def __init__(self, reserva_conflictiva_id: str):
        self.reserva_conflictiva_id = reserva_conflictiva_id
        super().__init__(
            f"El intervalo se superpone con la reserva {reserva_conflictiva_id}."
        )


class ReservaNoEncontradaError(LookupError):
    """Indica que no existe una reserva con el identificador indicado."""


class ReservaYaCanceladaError(ValueError):
    """Indica que la reserva ya estaba cancelada."""


def _obtener_ahora_utc(ahora: datetime | None) -> datetime:
    momento = ahora if ahora is not None else datetime.now(timezone.utc)
    if momento.tzinfo is None or momento.utcoffset() is None:
        raise ValidacionTemporalError("El reloj debe proporcionar un instante con zona horaria.")
    return momento.astimezone(timezone.utc)


def crear_reserva(
    equipo_id: str,
    solicitante: str,
    fecha_inicio: str,
    hora_inicio: str,
    fecha_fin: str,
    hora_fin: str,
    *,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    ahora: datetime | None = None,
) -> str:
    if not isinstance(solicitante, str) or not solicitante.strip():
        raise SolicitanteInvalidoError("El solicitante no puede estar vacío.")

    momento_utc = _obtener_ahora_utc(ahora)
    intervalo: IntervaloUTC = validar_intervalo(
        fecha_inicio,
        hora_inicio,
        fecha_fin,
        hora_fin,
        ahora=momento_utc,
    )
    reserva_id = str(uuid4())
    creada_utc = momento_utc.isoformat(timespec=FORMATO_UTC)
    connection = connect(database_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        equipment = connection.execute(
            "SELECT 1 FROM equipos WHERE id = ?", (equipo_id,)
        ).fetchone()
        if equipment is None:
            raise EquipoNoEncontradoError(f"El equipo {equipo_id} no existe.")

        conflict = buscar_reserva_conflictiva(connection, equipo_id, intervalo)
        if conflict is not None:
            raise ReservaSuperpuestaError(conflict["id"])

        connection.execute(
            """
            INSERT INTO reservas (
                id, equipo_id, solicitante, inicio_utc, fin_utc,
                estado, creada_utc, cancelada_utc
            ) VALUES (?, ?, ?, ?, ?, 'activa', ?, NULL)
            """,
            (
                reserva_id,
                equipo_id,
                solicitante,
                intervalo.inicio_utc,
                intervalo.fin_utc,
                creada_utc,
            ),
        )
        connection.commit()
        return reserva_id
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        connection.close()


def cancelar_reserva(
    reserva_id: str,
    *,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    ahora: datetime | None = None,
) -> None:
    cancelada_utc = _obtener_ahora_utc(ahora).isoformat(timespec=FORMATO_UTC)
    connection = connect(database_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        reservation = connection.execute(
            "SELECT estado FROM reservas WHERE id = ?", (reserva_id,)
        ).fetchone()
        if reservation is None:
            raise ReservaNoEncontradaError(f"La reserva {reserva_id} no existe.")
        if reservation["estado"] == "cancelada":
            raise ReservaYaCanceladaError(f"La reserva {reserva_id} ya está cancelada.")

        connection.execute(
            """
            UPDATE reservas
            SET estado = 'cancelada', cancelada_utc = ?
            WHERE id = ? AND estado = 'activa'
            """,
            (cancelada_utc, reserva_id),
        )
        connection.commit()
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        connection.close()