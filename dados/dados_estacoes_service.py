from . import dados_estacoes_provider as provider
from pystreamapi import Stream

dados: list[dict]

def get_dados(data_inicial: str, data_final: str, cod_estacao: str, token: str) -> dict | None:
    dados = provider.get(data_inicial, data_final, cod_estacao, token)
    return dados