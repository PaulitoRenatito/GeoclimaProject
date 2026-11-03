"""Aggregations behind the charts and the map. Pure functions over records, no UI code."""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from statistics import fmean

from geoclima.weather.domain.models import WeatherData


@dataclass(frozen=True)
class Metric:
    field: str
    label: str
    unit: str
    # How a station's daily values become one number for the period: rain adds up, the rest average.
    aggregate: Callable[[list[float]], float]

    @property
    def period_note(self) -> str:
        return "total do período" if self.aggregate is sum else "média do período"

    def value(self, record: WeatherData) -> float | None:
        value = getattr(record, self.field)
        return None if value is None else float(value)


METRICS = [
    Metric("temp_max", "Temperatura máxima", "°C", fmean),
    Metric("temp_avg", "Temperatura média", "°C", fmean),
    Metric("temp_min", "Temperatura mínima", "°C", fmean),
    Metric("precipitation", "Precipitação acumulada", "mm", sum),
    Metric("humidity_avg", "Umidade média", "%", fmean),
    Metric("wind_speed_avg", "Vento médio", "m/s", fmean),
]
METRICS_BY_LABEL = {metric.label: metric for metric in METRICS}


@dataclass(frozen=True)
class StationValue:
    code: str
    name: str
    value: float
    latitude: float | None
    longitude: float | None


@dataclass(frozen=True)
class Highlight:
    title: str
    value: str
    detail: str


def station_summary(records: list[WeatherData], metric: Metric) -> list[StationValue]:
    """One value per station for the whole period, highest first. Stations without data are left out."""
    values: dict[str, list[float]] = defaultdict(list)
    latest: dict[str, WeatherData] = {}
    for record in records:
        latest[record.station_code] = record
        value = metric.value(record)
        if value is not None:
            values[record.station_code].append(value)

    summary = [
        StationValue(
            code, latest[code].station_name, metric.aggregate(vals), latest[code].latitude, latest[code].longitude
        )
        for code, vals in values.items()
    ]
    return sorted(summary, key=lambda item: item.value, reverse=True)


def daily_series(
    records: list[WeatherData], metric: Metric, station_code: str | None = None
) -> list[tuple[date, float]]:
    """Daily values of one station, or the average across stations when station_code is None."""
    by_day: dict[date, list[float]] = defaultdict(list)
    for record in records:
        if station_code is not None and record.station_code != station_code:
            continue
        value = metric.value(record)
        if value is not None:
            by_day[record.measurement_date].append(value)
    return [(day, fmean(values)) for day, values in sorted(by_day.items())]


def describe_dataset(records: list[WeatherData]) -> str:
    if not records:
        return "Nenhum dado carregado"
    days = sorted({record.measurement_date for record in records})
    stations = {record.station_code for record in records}
    period = _fmt(days[0]) if len(days) == 1 else f"{_fmt(days[0])} a {_fmt(days[-1])}"
    return f"{len(stations)} estação(ões) · {period} · {len(records)} registro(s)"


def highlights(records: list[WeatherData]) -> list[Highlight]:
    """The few numbers worth reading first: extremes of the period and the rainiest station."""
    cards = []

    hottest = _extreme(records, "temp_max", max)
    if hottest:
        cards.append(Highlight("Maior máxima", f"{hottest.temp_max:.1f} °C", _where(hottest)))

    coldest = _extreme(records, "temp_min", min)
    if coldest:
        cards.append(Highlight("Menor mínima", f"{coldest.temp_min:.1f} °C", _where(coldest)))

    rain = station_summary(records, METRICS_BY_LABEL["Precipitação acumulada"])
    if rain:
        cards.append(Highlight("Mais chuva", f"{rain[0].value:.1f} mm", f"{rain[0].name} (acumulado)"))

    humidity = [r.humidity_avg for r in records if r.humidity_avg is not None]
    if humidity:
        cards.append(Highlight("Umidade média", f"{fmean(humidity):.0f} %", "média de todas as estações"))

    return cards


def _extreme(records: list[WeatherData], field: str, pick: Callable) -> WeatherData | None:
    candidates = [record for record in records if getattr(record, field) is not None]
    return pick(candidates, key=lambda record: getattr(record, field)) if candidates else None


def _where(record: WeatherData) -> str:
    return f"{record.station_name} em {_fmt(record.measurement_date)}"


def _fmt(day: date) -> str:
    return day.strftime("%d/%m/%Y")
