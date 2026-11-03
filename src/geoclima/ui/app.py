import queue
import threading
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter

from geoclima.credentials import TokenStore
from geoclima.exporter.reader import ExportReadError, read_export
from geoclima.preferences import PREFERENCES_PATH, Preferences
from geoclima.settings import OUTPUT_DIR
from geoclima.ui.frames.action_frame import ActionFrame
from geoclima.ui.frames.charts_frame import ChartsFrame
from geoclima.ui.frames.export_options_frame import ExportOptionsFrame
from geoclima.ui.frames.history_frame import HistoryFrame
from geoclima.ui.frames.input_frame import InputFrame
from geoclima.ui.frames.log_frame import LogFrame
from geoclima.ui.frames.map_frame import MapFrame, create_map_widget
from geoclima.ui.frames.progress_frame import ProgressFrame
from geoclima.ui.frames.station_selector_frame import StationSelectorFrame
from geoclima.ui.messages import MessageType, WorkerMessage
from geoclima.ui.widgets.exceptions import InputValidationError
from geoclima.ui.worker import CollectionJob, run_collection
from geoclima.weather.domain.models import WeatherData
from geoclima.weather.infrastructure.station_catalog import StationCatalog

QUEUE_POLL_MS = 100
CHARTS_TAB = "Gráficos"
MAP_TAB = "Mapa"


class WeatherApp(customtkinter.CTk):
    def __init__(
        self,
        output_dir: Path = OUTPUT_DIR,
        catalog: StationCatalog | None = None,
        token_store: TokenStore | None = None,
        preferences_path: Path = PREFERENCES_PATH,
        map_factory: Callable[[Any], Any] = create_map_widget,
    ):
        super().__init__()
        self.output_dir = output_dir
        self.catalog = catalog or StationCatalog()
        self.token_store = token_store or TokenStore()
        self.preferences_path = preferences_path
        self.preferences = Preferences.load(preferences_path)
        self.current_job: CollectionJob | None = None
        self.map_factory = map_factory

        self.title("Geoclima - Coletor de Dados Meteorológicos")
        self.geometry("1100x760")
        self.minsize(950, 680)

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

        # Tk widgets are not thread-safe: background threads only enqueue messages,
        # and the main loop applies them in process_queue.
        self.comm_queue: queue.Queue[WorkerMessage] = queue.Queue()
        self.create_widgets()
        self.apply_preferences()
        self.load_stations()
        self.after(QUEUE_POLL_MS, self.process_queue)

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tab_view = customtkinter.CTkTabview(self, corner_radius=6, command=self.on_tab_change)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        collector_tab = self.tab_view.add("Coleta de Dados")
        history_tab = self.tab_view.add("Histórico")
        charts_tab = self.tab_view.add(CHARTS_TAB)
        map_tab = self.tab_view.add(MAP_TAB)
        for tab in (charts_tab, map_tab):
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        collector_tab.grid_columnconfigure(0, weight=3, uniform="columns")
        collector_tab.grid_columnconfigure(1, weight=2, uniform="columns")
        collector_tab.grid_rowconfigure(4, weight=1)

        history_tab.grid_columnconfigure(0, weight=1)
        history_tab.grid_rowconfigure(0, weight=1)

        self.input_frame = InputFrame(collector_tab)
        self.input_frame.grid(row=0, column=0, sticky="new", padx=10, pady=(10, 5))

        self.export_options = ExportOptionsFrame(collector_tab)
        self.export_options.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.station_selector = StationSelectorFrame(collector_tab)
        self.station_selector.grid(row=0, column=1, rowspan=5, sticky="nsew", padx=10, pady=10)

        self.action_frame = ActionFrame(collector_tab, start_command=self.start_task, cancel_command=self.cancel_task)
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.progress_frame = ProgressFrame(collector_tab)
        self.progress_frame.grid(row=3, column=0, sticky="ew", padx=10)

        self.log_frame = LogFrame(collector_tab)
        self.log_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(5, 10))

        self.history_frame = HistoryFrame(history_tab, output_dir=self.output_dir, on_visualize=self.visualize_file)
        self.history_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.charts_frame = ChartsFrame(charts_tab, on_load_file=self.visualize_file, output_dir=self.output_dir)
        self.charts_frame.grid(row=0, column=0, sticky="nsew")

        self.map_frame = MapFrame(map_tab, map_factory=self.map_factory)
        self.map_frame.grid(row=0, column=0, sticky="nsew")

    def on_tab_change(self):
        if self.tab_view.get() == MAP_TAB:
            self.map_frame.show()

    def show_records(self, records: list[WeatherData], source: str = "Última coleta") -> None:
        """Feeds the charts and the map. Catalog coordinates fill in stations without a position."""
        coordinates = {
            s.code: (s.latitude, s.longitude)
            for s in self.station_selector.stations
            if s.latitude is not None and s.longitude is not None
        }
        self.charts_frame.set_records(records, source)
        self.map_frame.set_records(records, coordinates)

    def visualize_file(self, path: Path) -> None:
        try:
            records = read_export(path)
        except ExportReadError as e:
            messagebox.showerror("Arquivo inválido", str(e))
            return
        self.show_records(records, path.name)
        self.tab_view.set(CHARTS_TAB)

    def apply_preferences(self):
        self.export_options.set_values(self.preferences.format, self.preferences.mode)
        if self.preferences.remember_token:
            self.input_frame.set_token(self.token_store.load())

    def save_preferences(self, job: CollectionJob):
        remember = bool(self.input_frame.remember_token.get())
        if remember:
            self.token_store.save(job.token)
        elif self.preferences.remember_token:
            self.token_store.clear()

        self.preferences.state = self.station_selector.current_state
        self.preferences.export_format = job.export_format.name
        self.preferences.export_mode = job.export_mode.name
        self.preferences.remember_token = remember
        self.preferences.save(self.preferences_path)

    def load_stations(self):
        """Loads the catalog off the main thread: it may hit the network."""

        def load():
            result = self.catalog.load()
            self.comm_queue.put(WorkerMessage(MessageType.STATIONS_LOADED, result))

        threading.Thread(target=load, daemon=True).start()

    def process_queue(self):
        try:
            while True:
                self.handle_message(self.comm_queue.get_nowait())
        except queue.Empty:
            pass
        finally:
            self.after(QUEUE_POLL_MS, self.process_queue)

    def handle_message(self, message: WorkerMessage):
        match message.type:
            case MessageType.LOG:
                self.log_frame.log_message(message.payload)
            case MessageType.PROGRESS_START:
                self.progress_frame.set_maximum(message.payload)
            case MessageType.PROGRESS_STEP:
                self.progress_frame.step(message.payload)
            case MessageType.TASK_DONE:
                self.log_frame.show_success(message.payload)
                self.history_frame.populate_history()
            case MessageType.TASK_ERROR:
                self.log_frame.show_error(message.payload)
            case MessageType.TASK_CANCELLED:
                self.log_frame.show_warning(message.payload)
            case MessageType.TASK_FINISHED:
                self.current_job = None
                self.action_frame.set_running(False)
            case MessageType.STATIONS_LOADED:
                self.station_selector.set_catalog(message.payload, preferred_state=self.preferences.state)
            case MessageType.RECORDS_COLLECTED:
                self.show_records(message.payload)

    def build_job(self) -> CollectionJob:
        token, initial_date, final_date = self.input_frame.get_values()
        stations = self.station_selector.selected_stations()
        if not stations:
            raise InputValidationError("Selecione pelo menos uma estação.")
        return CollectionJob(
            token,
            initial_date,
            final_date,
            stations,
            self.output_dir,
            self.export_options.export_format,
            self.export_options.mode,
        )

    def start_task(self):
        try:
            job = self.build_job()
        except InputValidationError as e:
            messagebox.showwarning("Entrada Inválida", e.message)
            return

        self.save_preferences(job)
        self.current_job = job
        self.action_frame.set_running(True)
        self.progress_frame.reset()
        self.log_frame.reset()

        period = f"a data {job.initial_date}" if job.final_date is None else f"{job.initial_date} a {job.final_date}"
        self.log_frame.log_message(f"Iniciando coleta de {len(job.stations)} estação(ões) para {period}.")

        threading.Thread(target=run_collection, args=(job, self.comm_queue), daemon=True).start()

    def cancel_task(self):
        if self.current_job is not None:
            self.current_job.cancel_event.set()
            self.log_frame.log_message("Cancelando após a estação atual...")
