import time
from typing import Dict, Callable, Any

from data.domain.weather_data import WeatherData
from data.domain.weather_data_request import WeatherDataRequest
from data.infrastructure import weather_data_provider as provider


def get_weather_data(dados_request: WeatherDataRequest, token: str) -> WeatherData | None:
    return provider.get(
        dados_request.date,
        dados_request.station_code,
        token
    )

def get_weather_data_intermittently(
        dados_request: list[WeatherDataRequest],
        token: str,
        time_between_requests: float,
        on_event: Callable[[str, Dict[str, Any]], None] = None,
) -> list[WeatherData] | None:
    on_event("process_started", {"total_requests": len(dados_request)})

    def fetch_with_delay(request) -> WeatherData | None:
        timer = time.time()
        result = get_weather_data(request, token)
        elapsed = time.time() - timer

        on_event("request_completed", {
            "station_name": result.DC_NOME,
            "elapsed_time": elapsed
        })

        remaining_wait = time_between_requests - elapsed

        if remaining_wait > 0:
            while (time.time() - timer) < time_between_requests:
                time.sleep(0.1)

        return result

    dados_alt = [fetch_with_delay(request) for request in dados_request]
    on_event("process_completed", {"total_processed": len(dados_alt)})

    return dados_alt
