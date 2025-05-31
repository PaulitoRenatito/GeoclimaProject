import json

from dados import dados_estacoes_provider
from env.secrets import token

# response = estacoes_automaticas_service.get_code_by_state('MG')
response = dados_estacoes_provider.get('2025-05-25', '2025-05-25', 'A549', token)

print(json.dumps(response, indent=4))