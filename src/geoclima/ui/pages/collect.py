from datetime import date, datetime, timedelta
from html import escape

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from geoclima.exporter.service import ExportFormat, ExportMode
from geoclima.ui import theme
from geoclima.ui.progress import ProgressTracker
from geoclima.ui.theme import named, restyle
from geoclima.ui.validation import validate_date_range, validate_past_date, validate_token
from geoclima.ui.widgets.common import SegmentedControl, page_header, panel
from geoclima.ui.widgets.station_selector import StationSelector

START_TEXT = "Iniciar coleta"
CANCEL_TEXT = "Cancelar coleta"
CANCELLING_TEXT = "Cancelando..."
DATE_DISPLAY = "dd/MM/yyyy"
LOG_COLORS = {"info": theme.TEXT, "success": theme.SUCCESS, "warning": theme.WARNING, "error": theme.DANGER}
LOG_PREFIXES = {"warning": "AVISO: ", "error": "ERRO: "}


def date_edit(day: date) -> QDateEdit:
    edit = QDateEdit()
    edit.setCalendarPopup(True)
    edit.setDisplayFormat(DATE_DISPLAY)
    edit.setMaximumDate(QDate.currentDate().addDays(-1))  # INMET only has complete data for past days
    edit.setDate(QDate(day.year, day.month, day.day))
    edit.setMinimumWidth(130)
    return edit


class CollectPage(QWidget):
    """Token, period, stations and export options on the left of a progress area; emits start and cancel."""

    start_requested = Signal()
    cancel_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.running = False
        self.progress = ProgressTracker()

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)
        root.addLayout(page_header("Coleta de Dados", QLabel("Dados diários das estações automáticas do INMET")))

        columns = QHBoxLayout()
        columns.setSpacing(14)
        left = QVBoxLayout()
        left.setSpacing(14)
        left.addWidget(self._build_form())
        left.addWidget(self._build_export())
        left.addWidget(self._build_run(), 1)
        columns.addLayout(left, 3)

        stations, stations_layout = panel("Estações")
        self.station_selector = StationSelector()
        stations_layout.addWidget(self.station_selector)
        columns.addWidget(stations, 2)
        root.addLayout(columns, 1)

    def _build_form(self) -> QWidget:
        frame, layout = panel("Token e período")
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Token INMET"), 0, 0)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("Cole aqui o token da API do INMET")
        grid.addWidget(self.token_input, 0, 1, 1, 3)
        self.remember_token = QCheckBox("Lembrar token (Cofre de Credenciais do Windows)")
        grid.addWidget(self.remember_token, 1, 1, 1, 3)

        yesterday = date.today() - timedelta(days=1)
        grid.addWidget(QLabel("Data inicial"), 2, 0)
        self.initial_date = date_edit(yesterday)
        grid.addWidget(self.initial_date, 2, 1)
        self.period_check = QCheckBox("até")
        self.period_check.setToolTip("Coletar um período em vez de um único dia")
        self.period_check.toggled.connect(self.on_period_toggled)
        grid.addWidget(self.period_check, 2, 2)
        self.final_date = date_edit(yesterday)
        self.final_date.setEnabled(False)
        grid.addWidget(self.final_date, 2, 3)
        grid.setColumnStretch(4, 1)
        layout.addLayout(grid)
        layout.addWidget(named(QLabel("Marque “até” para coletar um período; sem ela, só a data inicial."), "hint"))
        return frame

    def _build_export(self) -> QWidget:
        frame, layout = panel("Exportação")
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.addWidget(QLabel("Formato"), 0, 0)
        self.format_control = SegmentedControl([f.value for f in ExportFormat])
        grid.addWidget(self.format_control, 0, 1)
        grid.addWidget(QLabel("Arquivos"), 0, 2)
        self.mode_control = SegmentedControl([m.value for m in ExportMode])
        grid.addWidget(self.mode_control, 0, 3)
        grid.setColumnStretch(4, 1)
        layout.addLayout(grid)
        return frame

    def _build_run(self) -> QWidget:
        frame, layout = panel("Execução")
        self.action_button = named(QPushButton(START_TEXT), "primary")
        self.action_button.setMinimumHeight(40)
        self.action_button.clicked.connect(self.on_action_clicked)
        layout.addWidget(self.action_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        self.status_label = named(QLabel(), "hint")
        layout.addWidget(self.status_label)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("O andamento da coleta aparece aqui.")
        layout.addWidget(self.log_view, 1)
        return frame

    def on_period_toggled(self, checked: bool) -> None:
        self.final_date.setEnabled(checked and not self.running)
        if checked and self.final_date.date() < self.initial_date.date():
            self.final_date.setDate(self.initial_date.date())

    def on_action_clicked(self) -> None:
        if self.running:
            self.action_button.setEnabled(False)
            self.action_button.setText(CANCELLING_TEXT)
            self.cancel_requested.emit()
        else:
            self.start_requested.emit()

    # Form ------------------------------------------------------------------

    def set_token(self, token: str | None) -> None:
        self.token_input.setText(token or "")
        self.remember_token.setChecked(bool(token))

    def set_dates(self, initial: date, final: date | None = None) -> None:
        self.initial_date.setDate(QDate(initial.year, initial.month, initial.day))
        self.period_check.setChecked(final is not None)
        if final is not None:
            self.final_date.setDate(QDate(final.year, final.month, final.day))

    def get_values(self, today: date | None = None) -> tuple[str, date, date | None]:
        """Validates the inputs and returns (token, initial_date, final_date or None)."""
        token = validate_token(self.token_input.text())
        initial: date = self.initial_date.date().toPython()  # type: ignore[assignment]
        final: date | None = self.final_date.date().toPython() if self.period_check.isChecked() else None  # type: ignore[assignment]
        for day in (initial, final):
            if day is not None:
                validate_past_date(day, today)
        validate_date_range(initial, final)
        return token, initial, final

    @property
    def export_format(self) -> ExportFormat:
        return ExportFormat(self.format_control.value)

    @property
    def export_mode(self) -> ExportMode:
        return ExportMode(self.mode_control.value)

    def set_export_options(self, fmt: ExportFormat, mode: ExportMode) -> None:
        self.format_control.set_value(fmt.value)
        self.mode_control.set_value(mode.value)

    # Run state -------------------------------------------------------------

    def set_running(self, running: bool) -> None:
        self.running = running
        self.action_button.setEnabled(True)
        self.action_button.setText(CANCEL_TEXT if running else START_TEXT)
        restyle(self.action_button, "danger" if running else "primary")
        for widget in (
            self.token_input,
            self.remember_token,
            self.initial_date,
            self.period_check,
            self.format_control,
            self.mode_control,
            self.station_selector,
        ):
            widget.setEnabled(not running)
        self.final_date.setEnabled(not running and self.period_check.isChecked())

    def start_progress(self, total: int) -> None:
        self.progress.start(total)
        self.progress_bar.setMaximum(self.progress.maximum)
        self.progress_bar.setValue(0)
        self.status_label.setText(self.progress.status)

    def step_progress(self, amount: int) -> None:
        self.progress.step(amount)
        self.progress_bar.setValue(self.progress.current)
        self.status_label.setText(self.progress.status)

    def reset_progress(self) -> None:
        self.progress.reset()
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        self.status_label.setText("")

    def log(self, text: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = escape(LOG_PREFIXES.get(level, "") + text)
        self.log_view.append(
            f'<span style="color:{theme.DISABLED}">{timestamp}</span>&nbsp; '
            f'<span style="color:{LOG_COLORS[level]}">{message}</span>'
        )

    def clear_log(self) -> None:
        self.log_view.clear()

    def log_text(self) -> str:
        return self.log_view.toPlainText()
