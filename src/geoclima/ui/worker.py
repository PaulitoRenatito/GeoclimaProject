"""Collection + export flow, run in a background thread. Talks to the GUI only through a queue."""

import logging
import threading
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from queue import Queue

from geoclima.exporter.service import ExportFormat, ExportMode, export_records
from geoclima.settings import OUTPUT_DIR
from geoclima.ui.messages import MessageType, WorkerMessage
from geoclima.weather.application.collection_service import CollectionCancelled, collect_weather_data
from geoclima.weather.domain.models import Station, WeatherData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectionJob:
    """Everything the worker needs, validated by the UI before the thread starts."""

    token: str
    initial_date: date
    final_date: date | None
    stations: list[Station]
    output_dir: Path = OUTPUT_DIR
    export_format: ExportFormat = ExportFormat.CSV
    export_mode: ExportMode = ExportMode.PER_DAY
    cancel_event: threading.Event = field(default_factory=threading.Event)


class QueueListener:
    """Adapts collection progress events to GUI queue messages."""

    def __init__(self, queue: Queue[WorkerMessage], station_names: dict[str, str] | None = None) -> None:
        self.queue = queue
        self.station_names = station_names or {}

    def on_start(self, total: int) -> None:
        self.queue.put(WorkerMessage(MessageType.PROGRESS_START, total))

    def on_station_result(self, station_code: str, records: list[WeatherData] | None) -> None:
        name = self.station_names.get(station_code, station_code)
        if records:
            text = f"Dados recebidos para: {records[0].station_name}"
        elif records is None:
            text = f"Falha ao obter dados da estação: {name}"
        else:
            text = f"Estação {name} sem dados no período."
        self.queue.put(WorkerMessage(MessageType.LOG, text))
        self.queue.put(WorkerMessage(MessageType.PROGRESS_STEP, 1))


def run_collection(job: CollectionJob, queue: Queue[WorkerMessage]) -> None:
    try:
        records = collect_weather_data(
            token=job.token,
            initial_date=job.initial_date,
            final_date=job.final_date,
            station_codes=[station.code for station in job.stations],
            listener=QueueListener(queue, {station.code: station.name for station in job.stations}),
            cancel_event=job.cancel_event,
        )

        if not records:
            queue.put(
                WorkerMessage(MessageType.TASK_ERROR, "Nenhum dado foi retornado pela API. Verifique a data e o token.")
            )
            return

        queue.put(WorkerMessage(MessageType.LOG, f"Coleta finalizada. Exportando ({job.export_format.value})..."))
        paths = export_records(records, job.export_format, job.export_mode, job.output_dir)
        for path in paths:
            queue.put(WorkerMessage(MessageType.LOG, f"Arquivo '{path.name}' exportado."))

        queue.put(WorkerMessage(MessageType.RECORDS_COLLECTED, records))
        queue.put(
            WorkerMessage(
                MessageType.TASK_DONE, f"Exportação concluída: {len(paths)} arquivo(s) em '{job.output_dir}'."
            )
        )

    except CollectionCancelled:
        queue.put(WorkerMessage(MessageType.TASK_CANCELLED, "Coleta cancelada. Nenhum arquivo foi gerado."))
    except Exception as e:
        logger.exception("Collection failed")
        queue.put(WorkerMessage(MessageType.TASK_ERROR, f"Ocorreu um erro crítico: {e}"))
    finally:
        queue.put(WorkerMessage(MessageType.TASK_FINISHED))
