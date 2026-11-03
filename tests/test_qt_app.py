import os
from datetime import date, timedelta

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QMessageBox

from geoclima.credentials import TokenStore
from geoclima.exporter.service import ExportFormat, ExportMode, export_records
from geoclima.preferences import Preferences
from geoclima.qt.collect_page import CANCEL_TEXT, CANCELLING_TEXT, START_TEXT
from geoclima.qt.main_window import MainWindow
from geoclima.qt.progress import ProgressTracker, format_eta
from geoclima.ui.messages import MessageType, WorkerMessage
from geoclima.ui.widgets.exceptions import InputValidationError
from geoclima.ui.worker import run_collection
from geoclima.weather.domain.models import Station
from geoclima.weather.infrastructure.station_catalog import CatalogResult, CatalogSource
from tests.conftest import FakeKeyring, make_record

YESTERDAY = date.today() - timedelta(days=1)
STATIONS = [
    Station(code="A565", name="BAMBUI", state="MG", status="Operante", latitude=-20.03, longitude=-46.0),
    Station(code="A521", name="BELO HORIZONTE - PAMPULHA", state="MG", status="Operante"),
    Station(code="A999", name="QUEBRADA", state="MG", status="Pane"),
    Station(code="A422", name="ABROLHOS", state="BA", status="Operante"),
]


class FakeCatalog:
    def __init__(self, source=CatalogSource.API):
        self.source = source

    def load(self, force_refresh=False):
        return CatalogResult(STATIONS, self.source)


class ThreadStarter:
    """Runs the catalog load inline and records the collection instead of starting it."""

    def __init__(self):
        self.collections = []

    def __call__(self, target, args):
        if target is run_collection:
            self.collections.append(args)
        else:
            target(*args)


@pytest.fixture
def keyring():
    return FakeKeyring()


@pytest.fixture
def make_window(qtbot, tmp_path, keyring):
    def make(source=CatalogSource.API, preferences=None):
        prefs_path = tmp_path / "preferences.json"
        if preferences is not None:
            preferences.save(prefs_path)
        window = MainWindow(
            output_dir=tmp_path / "output",
            catalog=FakeCatalog(source),
            token_store=TokenStore(keyring),
            preferences_path=prefs_path,
            start_thread=ThreadStarter(),
        )
        qtbot.addWidget(window)
        return window

    return make


@pytest.fixture
def window(make_window):
    return make_window()


@pytest.fixture
def warnings(monkeypatch):
    shown = []
    monkeypatch.setattr(QMessageBox, "warning", lambda parent, title, text: shown.append(text))
    monkeypatch.setattr(QMessageBox, "critical", lambda parent, title, text: shown.append(text))
    return shown


def fill_form(window, token="my-token", initial=YESTERDAY, final=None):
    page = window.collect_page
    page.token_input.setText(token)
    page.set_dates(initial, final)


# Startup -------------------------------------------------------------------


def test_preferences_and_saved_token_are_restored_on_startup(make_window, keyring):
    keyring.set_password("Geoclima", "inmet-token", "saved-token")
    prefs = Preferences(state="BA", export_format="EXCEL", export_mode="SINGLE_FILE", remember_token=True)

    page = make_window(preferences=prefs).collect_page

    assert page.token_input.text() == "saved-token"
    assert page.remember_token.isChecked()
    assert page.export_format is ExportFormat.EXCEL
    assert page.export_mode is ExportMode.SINGLE_FILE
    assert page.station_selector.current_state == "BA"


def test_defaults(window):
    page = window.collect_page
    assert page.initial_date.date().toPython() == YESTERDAY
    assert page.initial_date.maximumDate().toPython() == YESTERDAY
    assert not page.final_date.isEnabled()
    assert page.export_format is ExportFormat.CSV
    assert window.current_page == "Coleta de Dados"


# Form ----------------------------------------------------------------------


def test_form_returns_typed_values(window):
    fill_form(window, " my-token ", YESTERDAY - timedelta(days=3), YESTERDAY)

    assert window.collect_page.get_values() == ("my-token", YESTERDAY - timedelta(days=3), YESTERDAY)


def test_single_day_when_period_is_unchecked(window):
    fill_form(window)
    assert window.collect_page.get_values()[2] is None


@pytest.mark.parametrize(
    ("token", "initial", "final", "message"),
    [
        ("", YESTERDAY, None, "Token"),
        ("t", YESTERDAY, YESTERDAY - timedelta(days=2), "anterior à Data Inicial"),
    ],
)
def test_form_rejects_invalid_values(window, token, initial, final, message):
    fill_form(window, token, initial, final)
    with pytest.raises(InputValidationError, match=message):
        window.collect_page.get_values()


def test_form_rejects_today(window):
    fill_form(window)
    with pytest.raises(InputValidationError, match="anterior à data atual"):
        window.collect_page.get_values(today=YESTERDAY)


def test_period_checkbox_enables_final_date_not_before_initial(window):
    page = window.collect_page
    page.set_dates(YESTERDAY - timedelta(days=5))
    page.final_date.setDate(page.initial_date.date().addDays(-10))

    page.period_check.setChecked(True)

    assert page.final_date.isEnabled()
    assert page.final_date.date() == page.initial_date.date()


def test_invalid_input_shows_warning_and_starts_nothing(window, warnings):
    window.collect_page.action_button.click()

    assert warnings == ["O campo de Token não pode estar vazio."]
    assert window.current_job is None
    assert window.start_thread.collections == []


def test_requires_at_least_one_station(window, warnings):
    fill_form(window)
    window.collect_page.station_selector.set_visible(False)

    window.collect_page.action_button.click()

    assert warnings == ["Selecione pelo menos uma estação."]


# Start, cancel, remember token ---------------------------------------------


def test_start_builds_the_job_and_turns_the_button_into_cancel(window):
    fill_form(window, final=YESTERDAY)
    page = window.collect_page
    page.set_export_options(ExportFormat.EXCEL, ExportMode.SINGLE_FILE)

    page.action_button.click()

    ((job, bridge),) = window.start_thread.collections
    assert bridge is window.bridge
    assert [s.code for s in job.stations] == ["A565", "A521"]  # the station in "pane" starts unchecked
    assert (job.token, job.initial_date, job.final_date) == ("my-token", YESTERDAY, YESTERDAY)
    assert (job.export_format, job.export_mode) == (ExportFormat.EXCEL, ExportMode.SINGLE_FILE)
    assert page.action_button.text() == CANCEL_TEXT
    assert page.action_button.objectName() == "danger"
    assert not page.token_input.isEnabled()
    assert "Iniciando coleta de 2 estação(ões)" in page.log_text()


def test_cancel_sets_the_job_event(window):
    fill_form(window)
    page = window.collect_page
    page.action_button.click()
    job = window.current_job

    page.action_button.click()

    assert job.cancel_event.is_set()
    assert page.action_button.text() == CANCELLING_TEXT
    assert not page.action_button.isEnabled()

    window.bridge.put(WorkerMessage(MessageType.TASK_FINISHED))
    assert page.action_button.text() == START_TEXT
    assert page.token_input.isEnabled()
    assert window.current_job is None


def test_remember_token_saves_it_in_the_vault_and_preferences(window, keyring, tmp_path):
    fill_form(window, "secret")
    window.collect_page.remember_token.setChecked(True)

    window.collect_page.action_button.click()

    assert keyring.get_password("Geoclima", "inmet-token") == "secret"
    assert Preferences.load(tmp_path / "preferences.json").remember_token


def test_unchecking_remember_token_removes_it_from_the_vault(make_window, keyring):
    keyring.set_password("Geoclima", "inmet-token", "old")
    window = make_window(preferences=Preferences(remember_token=True))
    window.collect_page.remember_token.setChecked(False)

    window.collect_page.action_button.click()

    assert keyring.get_password("Geoclima", "inmet-token") is None


# Stations ------------------------------------------------------------------


def test_station_selector_defaults_to_operational_stations_of_mg(window):
    selector = window.collect_page.station_selector
    assert selector.current_state == "MG"
    assert selector.state_combo.isEnabled()
    assert [s.code for s in selector.selected_stations()] == ["A565", "A521"]
    assert selector.count_label.text() == "2 de 3 selecionadas"
    assert selector.proxy.rowCount() == 3
    assert selector.note_label.isHidden()


def test_station_selector_search_and_bulk_selection(window):
    selector = window.collect_page.station_selector

    selector.search("quebr")
    assert selector.proxy.rowCount() == 1
    selector.set_visible(True)
    selector.search("")
    selector.set_visible(False)
    selector.search("A5")
    selector.set_visible(True)

    assert [s.code for s in selector.selected_stations()] == ["A565", "A521"]
    assert selector.count_label.text() == "2 de 3 selecionadas"


def test_checking_an_item_updates_the_count(window):
    selector = window.collect_page.station_selector
    selector.items()[2].setCheckState(Qt.CheckState.Checked)
    assert selector.count_label.text() == "3 de 3 selecionadas"


def test_station_selector_switches_state(window):
    selector = window.collect_page.station_selector
    selector.state_combo.setCurrentText("BA")
    assert [s.code for s in selector.selected_stations()] == ["A422"]


def test_offline_catalog_shows_a_note(make_window):
    selector = make_window(CatalogSource.BUILT_IN).collect_page.station_selector
    assert "lista embutida" in selector.note_label.text()
    assert not selector.note_label.isHidden()


# Worker messages -----------------------------------------------------------


def test_worker_messages_update_the_window(window, monkeypatch):
    page = window.collect_page
    clock = iter([100.0, 110.0])
    monkeypatch.setattr(page.progress, "clock", lambda: next(clock))

    window.bridge.put(WorkerMessage(MessageType.PROGRESS_START, 4))
    window.bridge.put(WorkerMessage(MessageType.PROGRESS_STEP, 1))
    window.bridge.put(WorkerMessage(MessageType.LOG, "Dados recebidos para: BAMBUI"))
    window.bridge.put(WorkerMessage(MessageType.TASK_ERROR, "falhou"))
    window.bridge.put(WorkerMessage(MessageType.TASK_CANCELLED, "cancelada"))
    window.bridge.put(WorkerMessage(MessageType.TASK_DONE, "Exportação concluída"))

    assert page.progress_bar.value() == 1
    assert page.status_label.text() == "1/4 estações · ~30 s restantes"
    text = page.log_text()
    assert "Dados recebidos para: BAMBUI" in text
    assert "ERRO: falhou" in text
    assert "AVISO: cancelada" in text
    assert "Exportação concluída" in text


def test_collected_records_feed_the_charts(window):
    records = [make_record(date(2025, 8, 28)), make_record(date(2025, 8, 28), "A521", "BELO HORIZONTE")]

    window.bridge.put(WorkerMessage(MessageType.RECORDS_COLLECTED, records))

    assert window.charts_page.records == records
    assert window.charts_page.subtitle.text().startswith("Última coleta · 2 estação(ões)")


def test_visualize_file_opens_the_charts(window, tmp_path):
    (path,) = export_records([make_record(date(2025, 8, 28))], ExportFormat.CSV, ExportMode.SINGLE_FILE, tmp_path)

    window.visualize_file(path)

    assert window.current_page == "Gráficos"
    assert window.charts_page.subtitle.text().startswith(path.name)


def test_visualize_invalid_file_shows_error(window, tmp_path, warnings):
    path = tmp_path / "outro.csv"
    path.write_text("a,b\n1,2\n")

    window.visualize_file(path)

    assert "não parece ser um arquivo exportado" in warnings[0]
    assert window.current_page == "Coleta de Dados"


def test_navigation(window):
    window.nav_buttons["Gráficos"].click()
    assert window.current_page == "Gráficos"


# Progress ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("seconds", "text"), [(44.6, "~45 s restantes"), (125, "~2 min 05 s restantes"), (-3, "~0 s restantes")]
)
def test_format_eta(seconds, text):
    assert format_eta(seconds) == text


def test_progress_tracker():
    clock = iter([0.0, 20.0, 30.0])
    tracker = ProgressTracker(lambda: next(clock))
    assert tracker.status == ""
    tracker.start(3)
    assert tracker.status == "0/3 estações"
    tracker.step()
    assert tracker.status == "1/3 estações · ~40 s restantes"
    tracker.step(5)
    assert tracker.status == "3/3 estações"


# Charts page ---------------------------------------------------------------


@pytest.fixture
def charts(window):
    page = window.charts_page
    page.set_records(
        [
            make_record(date(2025, 8, 28)).model_copy(update={"temp_max": 30.0}),
            make_record(date(2025, 8, 29)).model_copy(update={"temp_max": 34.0}),
            make_record(date(2025, 8, 28), "A521", "BELO HORIZONTE").model_copy(update={"temp_max": 28.0}),
        ],
        "teste.xlsx",
    )
    return page


def test_charts_cards_ranking_and_station_menu(charts):
    assert charts.subtitle.text() == "teste.xlsx · 2 estação(ões) · 28/08/2025 a 29/08/2025 · 3 registro(s)"
    assert charts.cards.count() == 4
    assert [charts.ranking_model.item(row).text() for row in range(2)] == ["BAMBUI", "BELO HORIZONTE"]
    assert charts.ranking_model.item(0, 1).text() == "32.0"
    assert not charts.station_combo.isEnabled()


def test_charts_bar_tooltip(charts):
    # Bars are drawn bottom-up: index 0 is the lowest value.
    assert charts.tooltip_at(QPointF(10, 0)) == "<b>BELO HORIZONTE</b> (A521)<br>28.0 °C"
    assert charts.tooltip_at(QPointF(10, 5)) is None


def test_charts_station_evolution_with_average(charts):
    charts.show_station("BAMBUI")

    assert charts.over_time
    assert charts.station_combo.isEnabled()
    assert charts.ranking.selectionModel().selectedRows()[0].row() == 0
    assert charts.tooltip_at(QPointF(0, 30)) == "<b>28/08/2025</b><br>BAMBUI: 30.0 °C<br>Média das estações: 29.0 °C"


def test_charts_rain_and_empty_state(charts):
    charts.metric_combo.setCurrentText("Precipitação acumulada")
    charts.show_station("Média das estações")
    assert set(charts.hover_series) == {"Média das estações"}

    charts.set_records([], "")
    assert charts.subtitle.text() == "Nenhum dado carregado"
    assert charts.cards.count() == 0


def test_charts_open_file_button(
    charts, monkeypatch, qtbot, warnings
):  # warnings: the window then fails to read the fake path
    from geoclima.qt import charts_page

    monkeypatch.setattr(charts_page.QFileDialog, "getOpenFileName", lambda *a: ("C:/x/MG.csv", ""))
    with qtbot.waitSignal(charts.file_requested) as signal:
        charts.choose_file()
    assert signal.args[0].name == "MG.csv"

    monkeypatch.setattr(charts_page.QFileDialog, "getOpenFileName", lambda *a: ("", ""))
    with qtbot.assertNotEmitted(charts.file_requested):
        charts.choose_file()


# History page --------------------------------------------------------------


def export_sample(window, day=date(2025, 8, 28), fmt=ExportFormat.CSV, mtime=None):
    (path,) = export_records([make_record(day)], fmt, ExportMode.SINGLE_FILE, window.output_dir)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def history_names(page):
    return [page.model.item(row).text() for row in range(page.model.rowCount())]


def test_empty_history(window):
    page = window.history_page
    assert page.model.rowCount() == 0
    assert not page.empty_label.isHidden()
    assert page.table.isHidden()
    assert not page.visualize_button.isEnabled()


def test_history_lists_exports_newest_first_with_details(window):
    old = export_sample(window, date(2025, 8, 27), mtime=1_700_000_000)
    new = export_sample(window, date(2025, 8, 28), ExportFormat.EXCEL, mtime=1_800_000_000)
    (window.output_dir / "notas.txt").write_text("ignored")

    window.bridge.put(WorkerMessage(MessageType.TASK_DONE, "Exportação concluída"))

    page = window.history_page
    assert history_names(page) == [new.name, old.name]
    assert page.model.item(0, 1).text() == "Excel"
    assert page.model.item(1, 2).text().endswith(" B")
    assert page.summary_label.text() == "2 arquivo(s) na pasta output"
    assert not page.table.isHidden()


def test_history_sorts_by_size(window):
    export_sample(window, date(2025, 8, 27))
    big = export_sample(window, date(2025, 8, 28), ExportFormat.EXCEL)
    page = window.history_page
    page.refresh()

    page.table.sortByColumn(2, Qt.SortOrder.DescendingOrder)

    assert history_names(page)[0] == big.name


def test_history_actions(window, monkeypatch, qtbot):
    from geoclima.qt import history_page

    opened, revealed = [], []
    monkeypatch.setattr(history_page, "open_path", opened.append)
    monkeypatch.setattr(history_page, "reveal_path", revealed.append)
    path = export_sample(window)
    page = window.history_page
    page.refresh()
    page.table.selectRow(0)

    assert page.visualize_button.isEnabled()
    page.open_button.click()
    page.reveal_button.click()
    page.visualize_button.click()

    assert opened == [path]
    assert revealed == [path]
    assert window.current_page == "Gráficos"
    assert window.charts_page.subtitle.text().startswith(path.name)

    page.open_folder()
    assert opened[-1] == window.output_dir


def test_history_keeps_selection_on_refresh(window):
    export_sample(window, date(2025, 8, 27), mtime=1_700_000_000)
    second = export_sample(window, date(2025, 8, 28), mtime=1_800_000_000)
    page = window.history_page
    page.refresh()
    page.table.selectRow(0)

    page.refresh()

    assert page.selected_path() == second


@pytest.mark.parametrize(("size", "text"), [(10, "10 B"), (1536, "1.5 KB"), (3 * 1024 * 1024, "3.0 MB")])
def test_format_size(size, text):
    from geoclima.qt.history_page import format_size

    assert format_size(size) == text
