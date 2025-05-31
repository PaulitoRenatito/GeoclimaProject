import requests
from pydantic import TypeAdapter

from estacao.estacao import Estacao


def get() -> list[Estacao] | None:
    response = requests.get(build_url())

    if response.status_code == 200:
        response = response.json()
        estacoes_list_adapter = TypeAdapter(list[Estacao])
        return estacoes_list_adapter.validate_python(response)
    else:
        print(f"Erro: {response.status_code}")
        return None

def build_url() -> str:
    base_url: str = "https://apitempo.inmet.gov.br/"
    return f"{base_url}/estacoes/T"