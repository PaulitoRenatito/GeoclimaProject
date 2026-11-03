from datetime import date
from typing import Any

import pytest
from keyring.errors import KeyringError, PasswordDeleteError

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


class FakeKeyring:
    """In-memory stand-in for the keyring module, so tests never touch the real vault."""

    def __init__(self, fail=False):
        self.passwords = {}
        self.fail = fail

    def get_password(self, service, key):
        if self.fail:
            raise KeyringError("vault locked")
        return self.passwords.get((service, key))

    def set_password(self, service, key, value):
        if self.fail:
            raise KeyringError("vault locked")
        self.passwords[(service, key)] = value

    def delete_password(self, service, key):
        if (service, key) not in self.passwords:
            raise PasswordDeleteError("not found")
        del self.passwords[(service, key)]
