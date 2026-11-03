from datetime import date

import pytest
from pydantic import ValidationError

from geoclima.weather.domain.models import WeatherData


def test_parses_api_keys_into_typed_domain_fields(raw_record):
    record = WeatherData.model_validate(raw_record)

    assert record.station_name == "BAMBUI"
    assert record.station_code == "A565"
    assert record.measurement_date == date(2025, 8, 28)
    assert record.temp_avg == pytest.approx(20.7)
    assert record.humidity_min == pytest.approx(29.0)
    assert record.latitude == pytest.approx(-20.03138888)


@pytest.mark.parametrize("missing_value", [None, "", "   "])
def test_missing_measurements_become_none(raw_record, missing_value):
    raw_record["CHUVA"] = missing_value

    assert WeatherData.model_validate(raw_record).precipitation is None


def test_ignores_fields_the_app_does_not_use(raw_record):
    raw_record["VEN_RAJ"] = "8.1"

    assert not hasattr(WeatherData.model_validate(raw_record), "VEN_RAJ")


def test_rejects_non_numeric_measurement(raw_record):
    raw_record["TEMP_MED"] = "quente"

    with pytest.raises(ValidationError):
        WeatherData.model_validate(raw_record)
