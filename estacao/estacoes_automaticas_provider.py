import requests


def get() -> dict | None:
    response = requests.get(build_url())

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro: {response.status_code}")
        return None

def build_url() -> str:
    base_url: str = "https://apitempo.inmet.gov.br/"
    return f"{base_url}/estacoes/T"