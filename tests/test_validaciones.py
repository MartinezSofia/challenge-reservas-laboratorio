from datetime import datetime, timezone

import pytest

from app.validaciones import (
    ValidacionTemporalError,
    validar_fecha,
    validar_hora,
    validar_intervalo,
)


AHORA = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("value", ["2026-01-01", "2000-02-29"])
def test_validar_fecha_acepta_fechas_validas(value):
    assert validar_fecha(value).isoformat() == value


@pytest.mark.parametrize("value", ["2026-02-29", "2026-13-01", "01-01-2026", "2026-1-01"])
def test_validar_fecha_rechaza_fechas_invalidas(value):
    with pytest.raises(ValidacionTemporalError):
        validar_fecha(value)


@pytest.mark.parametrize("value", ["00:00", "09:05", "23:59"])
def test_validar_hora_acepta_horas_validas(value):
    assert validar_hora(value).strftime("%H:%M") == value


@pytest.mark.parametrize("value", ["24:00", "12:60", "9:05", "12", "12:00:00"])
def test_validar_hora_rechaza_horas_invalidas(value):
    with pytest.raises(ValidacionTemporalError):
        validar_hora(value)


def test_validar_intervalo_normaliza_a_iso_utc():
    interval = validar_intervalo(
        "2026-01-10", "10:00", "2026-01-10", "11:00", ahora=AHORA
    )

    assert interval.inicio_utc == "2026-01-10T13:00:00+00:00"
    assert interval.fin_utc == "2026-01-10T14:00:00+00:00"


@pytest.mark.parametrize(
    ("start_time", "end_time"),
    [("10:00", "10:00"), ("11:00", "10:00")],
)
def test_validar_intervalo_rechaza_inicio_igual_o_posterior_al_fin(
    start_time, end_time
):
    with pytest.raises(ValidacionTemporalError, match="inicio debe ser anterior"):
        validar_intervalo(
            "2026-01-10", start_time, "2026-01-10", end_time, ahora=AHORA
        )


def test_validar_intervalo_rechaza_inicio_pasado():
    with pytest.raises(ValidacionTemporalError, match="anterior al momento actual"):
        validar_intervalo(
            "2025-12-31", "20:59", "2025-12-31", "22:00", ahora=AHORA
        )


def test_validar_intervalo_permite_inicio_igual_al_momento_actual():
    interval = validar_intervalo(
        "2025-12-31", "21:00", "2025-12-31", "22:00", ahora=AHORA
    )

    assert interval.inicio_utc == AHORA.isoformat(timespec="seconds")


def test_validar_intervalo_permite_cruzar_medianoche():
    interval = validar_intervalo(
        "2026-01-10", "23:00", "2026-01-11", "01:00", ahora=AHORA
    )

    assert interval.inicio_utc == "2026-01-11T02:00:00+00:00"
    assert interval.fin_utc == "2026-01-11T04:00:00+00:00"