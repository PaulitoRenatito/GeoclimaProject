import json
import requests
from pydantic import TypeAdapter

from data.domain.weather_data import WeatherData


def get(data: str, cod_estacao: str, token: str) -> WeatherData:
    response = requests.get(build_url(data, cod_estacao, token))

    if response.status_code == 200:
        response_json = json.loads(response.content)[0]
        dados_list_adapter = TypeAdapter(WeatherData)
        return dados_list_adapter.validate_python(response_json)
    else:
        raise Exception(response.status_code)

def build_url(data: str, cod_estacao: str, token: str) -> str:
    base_url: str = "https://apitempo.inmet.gov.br"
    return f"{base_url}/token/estacao/diaria/{data}/{data}/{cod_estacao}/{token}"