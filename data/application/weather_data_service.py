import time
import logging
from typing import Dict, Callable, Any

from data.domain.weather_data import WeatherData
from data.domain.weather_data_request import WeatherDataRequest
from data.infrastructure import weather_data_provider as provider

# Configura um logger simples para registrar erros em um arquivo ou no console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_weather_data(dados_request: WeatherDataRequest, token: str) -> WeatherData | None:
    try:
        return provider.get(
            dados_request.date,
            dados_request.station_code,
            token
        )
    except Exception as e:
        # Se ocorrer um erro (ex: estação sem dados, erro na API), registra e continua
        logging.error(f"Falha ao buscar dados para a estação {dados_request.station_code}: {e}")
        return None

def get_weather_data_intermittently(
        dados_request: list[WeatherDataRequest],
        token: str,
        time_between_requests: float,
        on_event: Callable[[str, Dict[str, Any]], None] = None,
) -> list[WeatherData]:
    if on_event:
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
