import time
import logging
from queue import Queue

from ..domain.weather_data import WeatherData
from geoclima_weather.presentation.model.weather_data_request import WeatherDataRequest
from ..infrastructure.provider import weather_data_provider as provider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_weather_data_intermittently(
        dados_request: list[WeatherDataRequest],
        token: str,
        time_between_requests: float,
        progress_queue: Queue = None,
) -> list[WeatherData]:
    if progress_queue:
        progress_queue.put(('config_progress', len(dados_request)))

    results = []

    for request in dados_request:
        timer = time.time()
        result = get_weather_data(request, token)
        elapsed = time.time() - timer

        if progress_queue:
            if result:
                progress_queue.put(('log', f"Dados recebidos para: {result.DC_NOME}"))
            else:
                progress_queue.put(('log', f"Falha ao obter dados da estação: {request.station_code}"))
            progress_queue.put(('progress_step', 1))

        if result:
            results.append(result)

        remaining_wait = time_between_requests - elapsed
        if remaining_wait > 0:
            time.sleep(remaining_wait)

    return results

def get_weather_data(dados_request: WeatherDataRequest, token: str) -> WeatherData | None:
    try:
        return provider.get(
            dados_request.initial_date,
            dados_request.final_date,
            dados_request.station_code,
            token
        )
    except Exception as e:
        # Se ocorrer um erro (ex: estação sem dados, erro na API), registra e continua
        logging.error(e)
        return None
