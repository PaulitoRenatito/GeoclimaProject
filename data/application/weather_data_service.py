import time
import logging
from queue import Queue
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
        progress_queue: Queue = None,
) -> list[WeatherData]:
    if on_event:
        on_event("process_started", {"total_requests": len(dados_request)})

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
            if on_event:
                on_event("request_completed", {
                    "station_name": result.DC_NOME,
                    "elapsed_time": elapsed
                })

        remaining_wait = time_between_requests - elapsed
        if remaining_wait > 0:
            time.sleep(remaining_wait)

    if on_event:
        on_event("process_completed", {"total_processed": len(dados_request)})

    return results
