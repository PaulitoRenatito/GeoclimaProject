from typing import Dict, Any


def weather_data_logger(event: str, data: Dict[str, Any]) -> None:
    if event == "process_started":
        print(f"Iniciando processamento de {data['total_requests']} solicitações...")

    elif event == "request_started":
        print(f"Iniciando requisição para estação {data['station_code']} "
              f"(período: {data['initial_date']} a {data['end_date']})")

    elif event == "request_completed":
        print(f"Requisição para estação {data['station_name']} concluída em {data['elapsed_time']:.2f}s")

    elif event == "waiting":
        print(f"Aguardando {data['wait_time']:.2f}s antes da próxima requisição...")

    elif event == "process_completed":
        print(f"Processamento concluído. Total de {data['total_processed']} requisições processadas.")