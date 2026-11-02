import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone


ZONA_UTC_MENOS_TRES = timezone(timedelta(hours=-3), name="UTC-03:00")
FORMATO_UTC = "seconds"


class ValidacionTemporalError(ValueError):
    """Indica que una fecha, hora o intervalo no cumple el formato o las reglas."""


@dataclass(frozen=True)
class IntervaloUTC:
    inicio_utc: str
    fin_utc: str


def validar_fecha(valor: str) -> date:
    if not isinstance(valor, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor) is None:
        raise ValidacionTemporalError("La fecha debe tener formato AAAA-MM-DD.")
    try:
        return date.fromisoformat(valor)
    except ValueError as error:
        raise ValidacionTemporalError("La fecha no es válida.") from error


def validar_hora(valor: str) -> time:
    if not isinstance(valor, str) or re.fullmatch(r"\d{2}:\d{2}", valor) is None:
        raise ValidacionTemporalError("La hora debe tener formato HH:MM de 24 horas.")
    hora, minuto = (int(parte) for parte in valor.split(":"))
    if hora > 23 or minuto > 59:
        raise ValidacionTemporalError("La hora no es válida.")
    try:
        return time.fromisoformat(valor)
    except ValueError as error:
        raise ValidacionTemporalError("La hora no es válida.") from error


def validar_intervalo(
    fecha_inicio: str,
    hora_inicio: str,
    fecha_fin: str,
    hora_fin: str,
    *,
    ahora: datetime | None = None,
) -> IntervaloUTC:
    inicio_local = datetime.combine(
        validar_fecha(fecha_inicio),
        validar_hora(hora_inicio),
        tzinfo=ZONA_UTC_MENOS_TRES,
    )
    fin_local = datetime.combine(
        validar_fecha(fecha_fin),
        validar_hora(hora_fin),
        tzinfo=ZONA_UTC_MENOS_TRES,
    )

    inicio_utc = inicio_local.astimezone(timezone.utc)
    fin_utc = fin_local.astimezone(timezone.utc)
    if inicio_utc >= fin_utc:
        raise ValidacionTemporalError("El inicio debe ser anterior al fin.")

    momento_actual = ahora if ahora is not None else datetime.now(timezone.utc)
    if momento_actual.tzinfo is None or momento_actual.utcoffset() is None:
        raise ValidacionTemporalError("El reloj debe proporcionar un instante con zona horaria.")
    if inicio_utc < momento_actual.astimezone(timezone.utc):
        raise ValidacionTemporalError("El inicio no puede ser anterior al momento actual.")

    return IntervaloUTC(
        inicio_utc=inicio_utc.isoformat(timespec=FORMATO_UTC),
        fin_utc=fin_utc.isoformat(timespec=FORMATO_UTC),
    )