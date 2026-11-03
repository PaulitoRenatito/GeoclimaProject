from collections import defaultdict
from typing import Optional

from geoclima_exporter.csv_exporter import CsvExporter
from geoclima_exporter.exporter import OUTPUT_DIR
from geoclima_weather.presentation import weather_controller

def get_export_data(
        token: str,
        comm_queue,
        initial_date: str,
        final_date: Optional[str] = None,
):
    """
    Runs the collection and export flow in a worker thread.
    Talks to the GUI only through comm_queue.
    """
    try:
        dados_coletados = weather_controller.start_weather_data_collection(
            token=token,
            progress_queue=comm_queue,
            initial_date=initial_date,
            final_date=final_date,
        )

        data_by_date = defaultdict(list)
        for station_data in dados_coletados:
            for data in station_data:
                data_by_date[data.DT_MEDICAO].append(data)

        if not data_by_date:
            comm_queue.put(('task_error', "Nenhum dado foi retornado pela API. Verifique a data e o token."))
            return

        comm_queue.put(('log', f"Coleta finalizada. Exportando {len(data_by_date)} arquivo(s) CSV..."))

        for date, data in sorted(data_by_date.items()):
            exporter = CsvExporter(date=date, data=data)
            exporter.export()
            comm_queue.put(('log', f"Arquivo '{exporter.get_file_name()}' exportado."))

        comm_queue.put(('task_done', f"Exportação concluída. Arquivos salvos em '{OUTPUT_DIR}'."))

    except Exception as e:
        comm_queue.put(('task_error', f"Ocorreu um erro crítico: {e}"))
    finally:
        comm_queue.put(('enable_button', None))
