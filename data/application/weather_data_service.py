import time

from pystreamapi import Stream

from data.domain.weather_data_request import WeatherDataRequest
from data.infrastructure import weather_data_provider as provider
from data.domain.weather_data import WeatherData


def get_weather_data(dados_request: WeatherDataRequest, token: str) -> list[WeatherData] | None:
    return provider.get(
        dados_request.initial_date,
        dados_request.end_date,
        dados_request.station_code,
        token
    )

def get_weather_data_intermittently(
        dados_request: list[WeatherDataRequest],
        token: str,
        time_between_requests: float
) -> list[list[WeatherData]] | None:
    def fetch_with_delay(request) -> list[WeatherData] | None:
        timer = time.time()
        result = get_weather_data(request, token)
        while (time.time() - timer) < time_between_requests:
            # Ensure we wait for the specified time between requests
            pass
        return result

    dados_alt = Stream.of(dados_request).map(fetch_with_delay).to_list()

    return dados_alt