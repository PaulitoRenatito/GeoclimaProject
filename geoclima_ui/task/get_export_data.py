from collections import defaultdict
from typing import Optional

from geoclima_exporter.csv_exporter import CsvExporter
from geoclima_weather.presentation import weather_controller

def get_export_data(
        token: str,
        comm_queue,
        initial_date: str,
        final_date: Optional[str] = None,
):
    """
    Executa a lógica de coleta e exportação de dados.
    Comunica-se com a GUI através da fila (comm_queue).
    """
    try:
        dados_coletados = weather_controller.start_weather_data_collection(
            token=token,
            progress_queue=comm_queue,
            initial_date=initial_date,
            final_date=final_date,
        )

        if dados_coletados:
            comm_queue.put(('log', "Coleta finalizada. Exportando para Excel..."))

            all_data = [item for sublist in dados_coletados for item in sublist]
            data_by_date = defaultdict(list)
            for data in all_data:
                data_by_date[data.DT_MEDICAO].append(data)

            comm_queue.put(('log', f"Exportando {len(data_by_date)} arquivos..."))

            exported_files = []
            for date, data in data_by_date.items():
                exporter = CsvExporter(date=date, data=data)
                exporter.export()
                file_path = exporter.get_file_name()
                exported_files.append(file_path)
                comm_queue.put(('log', f"Arquivo '{file_path}' exportado."))

            comm_queue.put(('task_done', "Exportação concluída. Arquivos salvos na pasta 'csv'."))
        else:
            comm_queue.put(('task_error', "Nenhum dado foi retornado pela API. Verifique a data e o token."))

    except Exception as e:
        comm_queue.put(('task_error', f"Ocorreu um erro crítico: {e}"))
    finally:
        comm_queue.put(('enable_button', None))