import threading
from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from geoclima import __version__
from geoclima.credentials import TokenStore
from geoclima.exporter.reader import ExportReadError, read_export
from geoclima.preferences import PREFERENCES_PATH, Preferences
from geoclima.settings import OUTPUT_DIR
from geoclima.ui.messages import MessageType, WorkerMessage
from geoclima.ui.pages.charts import ChartsPage
from geoclima.ui.pages.collect import CollectPage
from geoclima.ui.pages.history import HistoryPage
from geoclima.ui.pages.map import MapPage
from geoclima.ui.theme import checkable, named
from geoclima.ui.validation import InputValidationError
from geoclima.ui.widgets.tile_map import Fetch
from geoclima.ui.worker import CollectionJob, run_collection
from geoclima.weather.domain.models import WeatherData
from geoclima.weather.infrastructure.station_catalog import CatalogResult, StationCatalog

COLLECT, HISTORY, CHARTS, MAP = "Coleta de Dados", "Histórico", "Gráficos", "Mapa"


class Catalog(Protocol):
    def load(self, force_refresh: bool = False) -> CatalogResult: ...


class MessageBridge(QObject):
    """Quacks like the queue run_collection writes to. Signals cross threads safely: slots run on the GUI thread."""

    received = Signal(object)

    def put(self, message: WorkerMessage) -> None:
        self.received.emit(message)


class MainWindow(QMainWindow):
    def __init__(
        self,
        output_dir: Path = OUTPUT_DIR,
        catalog: Catalog | None = None,
        token_store: TokenStore | None = None,
        preferences_path: Path = PREFERENCES_PATH,
        start_thread=lambda target, args: threading.Thread(target=target, args=args, daemon=True).start(),
        map_fetch: Fetch | None = None,
    ) -> None:
        super().__init__()
        self.output_dir = output_dir
        self.catalog: Catalog = catalog or StationCatalog()
        self.token_store = token_store or TokenStore()
        self.preferences_path = preferences_path
        self.preferences = Preferences.load(preferences_path)
        self.start_thread = start_thread
        self.current_job: CollectionJob | None = None

        self.setWindowTitle("Geoclima - Coletor de Dados Meteorológicos")
        self.resize(1280, 820)
        self.setMinimumSize(1100, 700)

        self.bridge = MessageBridge()
        self.bridge.received.connect(self.handle_message)

        self.collect_page = CollectPage()
        self.collect_page.start_requested.connect(self.start_task)
        self.collect_page.cancel_requested.connect(self.cancel_task)
        self.history_page = HistoryPage(output_dir=output_dir)
        self.history_page.visualize_requested.connect(self.visualize_file)
        self.charts_page = ChartsPage(output_dir=output_dir)
        self.charts_page.file_requested.connect(self.visualize_file)
        self.map_page = MapPage(map_fetch)

        self.pages = QStackedWidget()
        self.nav = QButtonGroup(self)
        self.nav_buttons: dict[str, QPushButton] = {}
        sidebar = self._build_sidebar()
        pages = (
            (COLLECT, self.collect_page),
            (HISTORY, self.history_page),
            (CHARTS, self.charts_page),
            (MAP, self.map_page),
        )
        for name, page in pages:
            self.add_page(name, page)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        self.apply_preferences()
        self.load_stations()

    # Navigation ------------------------------------------------------------

    def _build_sidebar(self) -> QFrame:
        sidebar = named(QFrame(), "sidebar")
        sidebar.setFixedWidth(210)
        self.side_layout = QVBoxLayout(sidebar)
        self.side_layout.setContentsMargins(10, 0, 10, 0)
        self.side_layout.setSpacing(4)
        self.side_layout.addWidget(named(QLabel("Geoclima"), "appTitle"))
        self.side_layout.addWidget(named(QLabel("Estações do INMET"), "appSubtitle"))
        self.side_layout.addStretch(1)
        self.side_layout.addWidget(named(QLabel(f"v{__version__}"), "version"))
        return sidebar

    def add_page(self, name: str, page: QWidget) -> None:
        button = checkable(QPushButton(name))
        button.clicked.connect(lambda: self.show_page(name))
        self.nav.addButton(button)
        self.nav_buttons[name] = button
        self.side_layout.insertWidget(self.side_layout.count() - 2, button)  # above the stretch and version
        self.pages.addWidget(page)
        if self.pages.count() == 1:
            button.setChecked(True)

    def show_page(self, name: str) -> None:
        self.nav_buttons[name].setChecked(True)
        self.pages.setCurrentIndex(list(self.nav_buttons).index(name))

    @property
    def current_page(self) -> str:
        return list(self.nav_buttons)[self.pages.currentIndex()]

    # Preferences -----------------------------------------------------------

    def apply_preferences(self) -> None:
        self.collect_page.set_export_options(self.preferences.format, self.preferences.mode)
        if self.preferences.remember_token:
            self.collect_page.set_token(self.token_store.load())

    def save_preferences(self, job: CollectionJob) -> None:
        remember = self.collect_page.remember_token.isChecked()
        if remember:
            self.token_store.save(job.token)
        elif self.preferences.remember_token:
            self.token_store.clear()

        self.preferences.state = self.collect_page.station_selector.current_state
        self.preferences.export_format = job.export_format.name
        self.preferences.export_mode = job.export_mode.name
        self.preferences.remember_token = remember
        self.preferences.save(self.preferences_path)

    # Background work -------------------------------------------------------

    def load_stations(self) -> None:
        """Loads the catalog off the GUI thread: it may hit the network."""

        def load() -> None:
            self.bridge.put(WorkerMessage(MessageType.STATIONS_LOADED, self.catalog.load()))

        self.start_thread(load, ())

    def handle_message(self, message: WorkerMessage) -> None:
        page = self.collect_page
        match message.type:
            case MessageType.LOG:
                page.log(message.payload)
            case MessageType.PROGRESS_START:
                page.start_progress(message.payload)
            case MessageType.PROGRESS_STEP:
                page.step_progress(message.payload)
            case MessageType.TASK_DONE:
                page.log(message.payload, "success")
                self.on_files_exported()
            case MessageType.TASK_ERROR:
                page.log(message.payload, "error")
            case MessageType.TASK_CANCELLED:
                page.log(message.payload, "warning")
            case MessageType.TASK_FINISHED:
                self.current_job = None
                page.set_running(False)
            case MessageType.STATIONS_LOADED:
                page.station_selector.set_catalog(message.payload, preferred_state=self.preferences.state)
            case MessageType.RECORDS_COLLECTED:
                self.show_records(message.payload)

    def on_files_exported(self) -> None:
        # The folder watcher only starts once the folder exists, which the first export creates.
        self.history_page.refresh()

    def build_job(self) -> CollectionJob:
        page = self.collect_page
        token, initial_date, final_date = page.get_values()
        stations = page.station_selector.selected_stations()
        if not stations:
            raise InputValidationError("Selecione pelo menos uma estação.")
        return CollectionJob(
            token, initial_date, final_date, stations, self.output_dir, page.export_format, page.export_mode
        )

    def start_task(self) -> None:
        try:
            job = self.build_job()
        except InputValidationError as e:
            QMessageBox.warning(self, "Entrada inválida", e.message)
            return

        self.save_preferences(job)
        self.current_job = job
        page = self.collect_page
        page.set_running(True)
        page.reset_progress()
        page.clear_log()
        period = (
            f"o dia {job.initial_date:%d/%m/%Y}"
            if job.final_date is None
            else (f"{job.initial_date:%d/%m/%Y} a {job.final_date:%d/%m/%Y}")
        )
        page.log(f"Iniciando coleta de {len(job.stations)} estação(ões) para {period}.")
        self.start_thread(run_collection, (job, self.bridge))

    def cancel_task(self) -> None:
        if self.current_job is not None:
            self.current_job.cancel_event.set()
            self.collect_page.log("Cancelando após a estação atual...")

    # Visualization ---------------------------------------------------------

    def show_records(self, records: list[WeatherData], source: str = "Última coleta") -> None:
        """Feeds the charts and the map. Catalog coordinates fill in stations without a position."""
        coordinates = {
            s.code: (s.latitude, s.longitude)
            for s in self.collect_page.station_selector.stations
            if s.latitude is not None and s.longitude is not None
        }
        self.charts_page.set_records(records, source)
        self.map_page.set_records(records, coordinates)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.map_page.map.shutdown()
        super().closeEvent(event)

    def visualize_file(self, path: Path) -> None:
        try:
            records = read_export(path)
        except ExportReadError as e:
            QMessageBox.critical(self, "Arquivo inválido", str(e))
            return
        self.show_records(records, path.name)
        self.show_page(CHARTS)
