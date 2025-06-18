import requests
from pydantic import TypeAdapter

from data.domain.weather_data import WeatherData


def get(data_inicial: str, data_final:str, cod_estacao: str, token: str) -> list[WeatherData] | None:
    response = requests.get(build_url(data_inicial, data_final, cod_estacao, token))

    if response.status_code == 200:
        response = response.json()
        dados_list_adapter = TypeAdapter(list[WeatherData])
        return dados_list_adapter.validate_python(response)
    else:
        print(f"Erro: {response.status_code}")
        return None

def build_url(data_inicial: str, data_final:str, cod_estacao: str, token: str) -> str:
    base_url: str = "https://apitempo.inmet.gov.br/"
    return f"{base_url}/token/estacao/diaria/{data_inicial}/{data_final}/{cod_estacao}/{token}"