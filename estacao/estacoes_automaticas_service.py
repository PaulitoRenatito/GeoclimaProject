from . import estacoes_automaticas_provider as provider
from pystreamapi import Stream

def get_by_state(estado: str) -> dict | None:
    return (Stream.of(provider.get())
            .filter(lambda estacao: estacao['SG_ESTADO'] == estado)
            .to_list())

def get_code_by_state(estado: str) -> dict | None:
    return (Stream.of(provider.get())
            .filter(lambda estacao: estacao['SG_ESTADO'] == estado)
            .map(lambda estacao: estacao['CD_ESTACAO'])
            .to_list())