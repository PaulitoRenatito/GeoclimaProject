import datetime
import json

import requests
from pydantic import TypeAdapter

from ...domain.weather_data import WeatherData
from ...infrastructure.model.GetDailyStationException import GetDailyStationException


def get(
    initial_date: datetime.date,
    final_date: datetime.date,
    station_code: str,
    token: str,
) -> WeatherData:
    response = requests.get(build_url(
        initial_date.strftime('%Y-%m-%d'),
        final_date.strftime('%Y-%m-%d'),
        station_code,
        token
    ))

    if response.status_code == 200:
        response_json = json.loads(response.content)[0]
        dados_list_adapter = TypeAdapter(WeatherData)
        return dados_list_adapter.validate_python(response_json)
    else:
        raise GetDailyStationException(
            f"Falha ao buscar dados para a estação {station_code}: {response.content}"
        )

def build_url(
        initial_date: str,
        final_date: str,
        station_code: str,
        token: str
) -> str:
    base_url: str = "https://apitempo.inmet.gov.br"
    return f"{base_url}/token/estacao/diaria/{initial_date}/{final_date}/{station_code}/{token}"