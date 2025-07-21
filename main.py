import os

from data.application import weather_data_service
from data.domain.weather_data_request import WeatherDataRequest
from data.infrastructure.weather_data_logger import weather_data_logger
from exporter.excel_exporter import ExcelExporter

try:
    from config import DATA_DA_BUSCA, INTERVALO_ENTRE_REQUISICOES
    from env.secrets import token
except ImportError:
    print("ERRO: Certifique-se de que os arquivos 'config.py' e 'secrets.py' existem.")
    print("Você pode criar 'secrets.py' a partir de 'secrets.py.example'.")
    exit()

from utils.constants import mg_stations_dict

def run():
    """Função principal que orquestra todo o processo."""
    print("=" * 50)
    print(f"Iniciando busca de dados para a data: {DATA_DA_BUSCA}")
    print("=" * 50)

    # Verifica se a pasta de saída 'excel' existe, se não, cria.
    if not os.path.exists('excel'):
        os.makedirs('excel')

    # 1. Preparar as requisições para cada estação
    requests = [
        WeatherDataRequest(date=DATA_DA_BUSCA, station_code=code)
        for name, code in mg_stations_dict.items()
    ]

    # 2. Chamar o serviço para buscar os dados
    # A função 'on_event' permite que a barra de progresso seja atualizada em tempo real.
    dados_coletados = weather_data_service.get_weather_data_intermittently(
        requests,
        token,
        INTERVALO_ENTRE_REQUISICOES,
        on_event=weather_data_logger
    )

    # 3. Exportar os dados para Excel, se algum dado foi coletado
    if dados_coletados:
        print("\nColeta finalizada. Exportando dados para a planilha...")
        exporter = ExcelExporter(
            date=DATA_DA_BUSCA,
            data=dados_coletados
        )
        exporter.export()
    else:
        print("\nNenhum dado foi coletado. Verifique a data ou o log de erros.")
        print("Nenhum arquivo foi gerado.")

if __name__ == "__main__":
    # Esta construção garante que o código só rode quando o arquivo é executado diretamente.
    run()