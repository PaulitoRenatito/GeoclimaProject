from datetime import date
from typing import Any

import pytest

from geoclima.weather.domain.models import WeatherData


def make_raw_record(**overrides: Any) -> dict[str, Any]:
    """A daily record shaped like the INMET API response (numbers as strings)."""
    record: dict[str, Any] = {
        "DC_NOME": "BAMBUI",
        "CD_ESTACAO": "A565",
        "UF": "MG",
        "DT_MEDICAO": "2025-08-28",
        "VL_LATITUDE": "-20.03138888",
        "VL_LONGITUDE": "-46.00888888",
        "TEMP_MED": "20.7",
        "TEMP_MIN": "11.7",
        "TEMP_MAX": "31.2",
        "UMID_MED": "63.4",
        "UMID_MIN": "29",
        "VEL_VENTO_MED": "1.2",
        "CHUVA": "0",
    }
    record.update(overrides)
    return record


def make_record(day: date, station_code: str = "A565", station_name: str = "BAMBUI") -> WeatherData:
    return WeatherData.model_validate(
        make_raw_record(DT_MEDICAO=day.isoformat(), CD_ESTACAO=station_code, DC_NOME=station_name)
    )


@pytest.fixture
def raw_record() -> dict[str, Any]:
    return make_raw_record()
