from pystreamapi import Stream

from dados.application import dados_estacoes_service
from dados.domain.dados_request import DadosRequest
from env.secrets import token
from exporter import csv_exporter

from utils.constants import mg_stations_codes
from utils.utils import get_file_name

data_inicial: str = '2025-05-25'
data_final: str = '2025-05-30'

requests = (Stream.of(mg_stations_codes)
            .map(lambda code: DadosRequest.builder()
                 .data_inicial(data_inicial)
                 .data_final(data_final)
                 .cod_estacao(code)
                 .build())
            .to_list())

response = dados_estacoes_service.get_dados_intermittently(requests, token, 1)


# Stream.of(response).for_each(lambda dados: csv_exporter.export(dados, get_file_name(dados[0].DC_NOME, data_inicial, data_final)))
