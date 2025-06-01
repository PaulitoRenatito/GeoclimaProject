from dados.domain.dados_request import DadosRequest
from dados.infrastructure import dados_estacoes_provider
from env.secrets import token
from exporter import csv_exporter

from utils import utils

data_inicial: str = '2025-05-25'
data_final: str = '2025-05-30'

# response = estacoes_automaticas_service.get_code_by_state('MG')
response = dados_estacoes_provider.get(data_inicial, data_final, 'A549', token)
# response = estacoes_automaticas_provider.get()

print(*response, sep='\n')

filename = f"{utils.normalize_str(response[0].DC_NOME.replace(' ', '_'))}_{data_inicial.replace('-', '_')}_ate_{data_final.replace('-', '_')}.csv"

csv_exporter.export(response, filename)