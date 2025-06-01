import time

from pystreamapi import Stream

from dados.domain.dados_request import DadosRequest
from dados.infrastructure import dados_estacoes_provider as provider
from dados.domain.dados import Dados


def get_dados(dados_request: DadosRequest, token: str) -> list[Dados] | None:
    return provider.get(
        dados_request.data_inicial,
        dados_request.data_final,
        dados_request.cod_estacao,
        token
    )

def get_dados_intermittently(
        dados_request: list[DadosRequest],
        token: str,
        time_between_requests: float
) -> list[list[Dados]] | None:
    def fetch_with_delay(request) -> list[Dados] | None:
        timer = time.time()
        result = get_dados(request, token)
        print(result)
        while (time.time() - timer) < time_between_requests:
            # Ensure we wait for the specified time between requests
            pass
        return result

    dados_alt = Stream.of(dados_request).map(fetch_with_delay).to_list()

    return dados_alt