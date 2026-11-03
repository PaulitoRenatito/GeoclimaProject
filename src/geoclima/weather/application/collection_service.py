"""Use case: collect the daily data of many stations from INMET, respecting a rate limit."""
import logging
import time
from collections.abc import Callable, Iterable
from datetime import date
from typing import Protocol

from geoclima.weather.domain.models import WeatherData, WeatherDataRequest
from geoclima.weather.infrastructure import inmet_client
from geoclima.weather.infrastructure.stations import MG_STATIONS

logger = logging.getLogger(__name__)

# Minimum interval between two requests, to stay polite with the INMET API.
DEFAULT_REQUEST_INTERVAL = 0.8

Fetcher = Callable[[date, date, str, str], list[WeatherData]]


class CollectionListener(Protocol):
    """Receives progress events. Keeps the use case independent from the UI."""

    def on_start(self, total: int) -> None: ...

    def on_station_result(self, station_code: str, records: list[WeatherData] | None) -> None:
        """records is None when the request failed, and empty when the station has no data."""
        ...


def collect_weather_data(
    token: str,
    initial_date: date,
    final_date: date | None = None,
    station_codes: Iterable[str] = MG_STATIONS.values(),
    listener: CollectionListener | None = None,
    request_interval: float = DEFAULT_REQUEST_INTERVAL,
    fetch: Fetcher = inmet_client.fetch_daily_data,
) -> list[WeatherData]:
    """
    Fetches every station sequentially and returns all records found.

    A failing station is logged and skipped, so one bad station never aborts the whole run.
    """
    requests = [
        WeatherDataRequest(
            initial_date=initial_date,
            final_date=final_date or initial_date,
            station_code=code,
        )
        for code in station_codes
    ]

    if listener:
        listener.on_start(len(requests))

    records: list[WeatherData] = []
    for request in requests:
        started_at = time.monotonic()
        result = _fetch_station(request, token, fetch)

        if result:
            records.extend(result)
        if listener:
            listener.on_station_result(request.station_code, result)

        remaining_wait = request_interval - (time.monotonic() - started_at)
        if remaining_wait > 0:
            time.sleep(remaining_wait)

    return records


def _fetch_station(request: WeatherDataRequest, token: str, fetch: Fetcher) -> list[WeatherData] | None:
    try:
        return fetch(request.initial_date, request.final_date, request.station_code, token)
    except Exception:
        logger.exception("Could not fetch station %s", request.station_code)
        return None
