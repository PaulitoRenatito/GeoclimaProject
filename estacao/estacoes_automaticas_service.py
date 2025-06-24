import estacoes_automaticas_provider as provider

from estacao import Estacao


def get_by_state(estado: str) -> list[Estacao] | None:
    return [estacao for estacao in provider.get() if estacao.SG_ESTADO == estado]


def get_code_by_state(estado: str) -> list[Estacao] | None:
    return [estacao.CD_ESTACAO for estacao in provider.get() if estacao.SG_ESTADO == estado]
