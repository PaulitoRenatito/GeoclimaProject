import requests


def get(data_inicial: str, data_final:str, cod_estacao: str, token: str) -> dict | None:
    response = requests.get(build_url(data_inicial, data_final, cod_estacao, token))

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro: {response.status_code}")
        return None

def build_url(data_inicial: str, data_final:str, cod_estacao: str, token: str) -> str:
    base_url: str = "https://apitempo.inmet.gov.br/"
    return f"{base_url}/token/estacao/{data_inicial}/{data_final}/{cod_estacao}/{token}"