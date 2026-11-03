import datetime

import requests
from pydantic import TypeAdapter
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...domain.weather_data import WeatherData
from ...infrastructure.model.GetDailyStationException import GetDailyStationException

BASE_URL = "https://apitempo.inmet.gov.br"

# (connect, read) timeouts in seconds. Without them a stalled API hangs the worker forever.
REQUEST_TIMEOUT = (10, 30)

_weather_data_list_adapter = TypeAdapter(list[WeatherData])


def _build_session() -> requests.Session:
    """Creates a session that retries transient failures with exponential backoff."""
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


_session = _build_session()


def get(
    initial_date: datetime.date,
    final_date: datetime.date,
    station_code: str,
    token: str,
) -> list[WeatherData]:
    url = build_url(
        initial_date.strftime('%Y-%m-%d'),
        final_date.strftime('%Y-%m-%d'),
        station_code,
        token,
    )

    try:
        response = _session.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        # The token is part of the URL, and requests exceptions embed the URL.
        # Re-raise with only the exception type so the token never reaches logs or the UI.
        raise GetDailyStationException(
            f"Falha de conexão ao buscar dados da estação {station_code} ({type(e).__name__})"
        ) from None

    if response.status_code == 204:
        return []

    if response.status_code != 200:
        raise GetDailyStationException(
            f"Falha ao buscar dados para a estação {station_code}: HTTP {response.status_code}"
        )

    if not response.content.strip():
        return []

    return _weather_data_list_adapter.validate_json(response.content)


def build_url(
        initial_date: str,
        final_date: str,
        station_code: str,
        token: str
) -> str:
    return f"{BASE_URL}/token/estacao/diaria/{initial_date}/{final_date}/{station_code}/{token}"
