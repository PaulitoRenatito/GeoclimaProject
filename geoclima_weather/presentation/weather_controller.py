from datetime import datetime
from queue import Queue

from config import INTERVALO_ENTRE_REQUISICOES
from geoclima_weather.presentation.model.weather_data_request import WeatherDataRequest
from ..application import weather_data_service
from ..infrastructure.util.constants import mg_stations_dict


def start_weather_data_collection(
        token: str,
        progress_queue: Queue,
        initial_date: str,
        final_date: str = None,
):
    """
    Starts the collection of weather data for a given date and token.
    """
    if final_date is None:
        final_date = initial_date

    initial_date = datetime.strptime(initial_date, '%Y-%m-%d').date()
    final_date = datetime.strptime(final_date, '%Y-%m-%d').date()

    requests = [
        WeatherDataRequest(
            initial_date=initial_date,
            final_date=final_date,
            station_code=code,
        )
        for name, code in mg_stations_dict.items()
    ]

    dados_coletados = weather_data_service.get_weather_data_intermittently(
        requests,
        token,
        INTERVALO_ENTRE_REQUISICOES,
        progress_queue=progress_queue
    )

    if not dados_coletados:
        raise ValueError("Nenhum dado foi retornado pela API. Verifique a data e o token.")

    return dados_coletados