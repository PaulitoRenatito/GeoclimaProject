from datetime import date

import pytest

from geoclima.ui.colors import value_colors
from geoclima.weather.application.analysis import (
    METRICS_BY_LABEL,
    daily_series,
    describe_dataset,
    highlights,
    station_summary,
)
from tests.conftest import make_record

DAY1, DAY2 = date(2025, 8, 28), date(2025, 8, 29)
TEMP_MAX = METRICS_BY_LABEL["Temperatura máxima"]
RAIN = METRICS_BY_LABEL["Precipitação acumulada"]


def record(day, code, name, **values):
    return make_record(day, code, name).model_copy(update=values)


@pytest.fixture
def records():
    return [
        record(DAY1, "A1", "ALFA", temp_max=30.0, temp_min=15.0, precipitation=2.0, humidity_avg=60.0),
        record(DAY2, "A1", "ALFA", temp_max=34.0, temp_min=17.0, precipitation=3.0, humidity_avg=70.0),
        record(DAY1, "B2", "BETA", temp_max=28.0, temp_min=12.0, precipitation=10.0, humidity_avg=80.0),
        record(DAY2, "B2", "BETA", temp_max=None, temp_min=None, precipitation=None, humidity_avg=None),
    ]


def test_station_summary_averages_temperature_and_ignores_missing(records):
    summary = station_summary(records, TEMP_MAX)

    assert [(s.code, s.value) for s in summary] == [("A1", 32.0), ("B2", 28.0)]
    assert summary[0].latitude == pytest.approx(-20.03138888)


def test_station_summary_adds_up_rain(records):
    assert [(s.code, s.value) for s in station_summary(records, RAIN)] == [("B2", 10.0), ("A1", 5.0)]


def test_daily_series_for_a_station_and_for_the_average(records):
    assert daily_series(records, TEMP_MAX, "A1") == [(DAY1, 30.0), (DAY2, 34.0)]
    assert daily_series(records, TEMP_MAX) == [(DAY1, 29.0), (DAY2, 34.0)]


def test_highlights(records):
    cards = {card.title: card for card in highlights(records)}

    assert cards["Maior máxima"].value == "34.0 °C"
    assert cards["Maior máxima"].detail == "ALFA em 29/08/2025"
    assert cards["Menor mínima"].value == "12.0 °C"
    assert cards["Mais chuva"].detail == "BETA (acumulado)"
    assert cards["Umidade média"].value == "70 %"


def test_highlights_and_description_without_data():
    assert highlights([]) == []
    assert describe_dataset([]) == "Nenhum dado carregado"


def test_describe_dataset(records):
    assert describe_dataset(records) == "2 estação(ões) · 28/08/2025 a 29/08/2025 · 4 registro(s)"
    assert describe_dataset(records[:1]) == "1 estação(ões) · 28/08/2025 · 1 registro(s)"


def test_period_note():
    assert TEMP_MAX.period_note == "média do período"
    assert RAIN.period_note == "total do período"


def test_value_colors_go_from_cold_to_hot():
    low, _mid, high = value_colors([10.0, 20.0, 30.0], TEMP_MAX)

    assert low != high
    assert int(low[1:3], 16) < int(high[1:3], 16)  # more red at the top of the scale
    assert value_colors([], TEMP_MAX) == []
    assert len(set(value_colors([5.0, 5.0], RAIN))) == 1  # equal values: no division by zero
