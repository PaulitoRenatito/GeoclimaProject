"""Collection + export flow, run in a background thread. Talks to the GUI only through a queue."""

import logging
from collections import defaultdict
from datetime import date
from pathlib import Path
from queue import Queue

from geoclima.exporter.csv_exporter import CsvExporter
from geoclima.settings import OUTPUT_DIR
from geoclima.ui.messages import MessageType, WorkerMessage
from geoclima.weather.application.collection_service import collect_weather_data
from geoclima.weather.domain.models import WeatherData

logger = logging.getLogger(__name__)


class QueueListener:
    """Adapts collection progress events to GUI queue messages."""

    def __init__(self, queue: Queue[WorkerMessage]) -> None:
        self.queue = queue

    def on_start(self, total: int) -> None:
        self.queue.put(WorkerMessage(MessageType.PROGRESS_START, total))

    def on_station_result(self, station_code: str, records: list[WeatherData] | None) -> None:
        if records:
            text = f"Dados recebidos para: {records[0].station_name}"
        elif records is None:
            text = f"Falha ao obter dados da estação: {station_code}"
        else:
            text = f"Estação {station_code} sem dados no período."
        self.queue.put(WorkerMessage(MessageType.LOG, text))
        self.queue.put(WorkerMessage(MessageType.PROGRESS_STEP, 1))


def run_collection(
    token: str,
    queue: Queue[WorkerMessage],
    initial_date: date,
    final_date: date | None = None,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    try:
        records = collect_weather_data(
            token=token,
            initial_date=initial_date,
            final_date=final_date,
            listener=QueueListener(queue),
        )

        records_by_day: dict[date, list[WeatherData]] = defaultdict(list)
        for record in records:
            records_by_day[record.measurement_date].append(record)

        if not records_by_day:
            queue.put(
                WorkerMessage(
                    MessageType.TASK_ERROR,
                    "Nenhum dado foi retornado pela API. Verifique a data e o token.",
                )
            )
            return

        queue.put(
            WorkerMessage(
                MessageType.LOG,
                f"Coleta finalizada. Exportando {len(records_by_day)} arquivo(s) CSV...",
            )
        )

        for day, day_records in sorted(records_by_day.items()):
            path = CsvExporter(day=day, data=day_records, output_dir=output_dir).export()
            queue.put(WorkerMessage(MessageType.LOG, f"Arquivo '{path.name}' exportado."))

        queue.put(
            WorkerMessage(
                MessageType.TASK_DONE,
                f"Exportação concluída. Arquivos salvos em '{output_dir}'.",
            )
        )

    except Exception as e:
        logger.exception("Collection failed")
        queue.put(WorkerMessage(MessageType.TASK_ERROR, f"Ocorreu um erro crítico: {e}"))
    finally:
        queue.put(WorkerMessage(MessageType.TASK_FINISHED))
