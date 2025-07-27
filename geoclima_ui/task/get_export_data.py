from geoclima_exporter.csv_exporter import CsvExporter
from geoclima_weather.presentation import weather_controller

def get_export_data(token, date_str, comm_queue):
    """
    Executa a lógica de coleta e exportação de dados.
    Comunica-se com a GUI através da fila (comm_queue).
    """
    try:
        dados_coletados = weather_controller.start_weather_data_collection(
            token=token,
            progress_queue=comm_queue,
            initial_date=date_str,
        )

        if dados_coletados:
            comm_queue.put(('log', "Coleta finalizada. Exportando para Excel..."))

            exporter = CsvExporter(date=date_str, data=dados_coletados)
            exporter.export()
            file_path = exporter.get_file_name()
            comm_queue.put(('task_done', file_path))
        else:
            comm_queue.put(('task_error', "Nenhum dado foi retornado pela API. Verifique a data e o token."))

    except Exception as e:
        comm_queue.put(('task_error', f"Ocorreu um erro crítico: {e}"))
    finally:
        comm_queue.put(('enable_button', None))