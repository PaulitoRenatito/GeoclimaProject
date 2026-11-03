"""Smoke tests of the real Tk window. Skipped where no display is available."""

import os
import time
import tkinter
from datetime import date, timedelta
from typing import ClassVar

import customtkinter
import pytest

from geoclima.credentials import TokenStore
from geoclima.exporter.service import ExportFormat, ExportMode
from geoclima.preferences import Preferences
from geoclima.ui import app as app_module
from geoclima.ui.frames import history_frame as history_module
from geoclima.ui.frames.action_frame import CANCEL_TEXT, START_TEXT
from geoclima.ui.frames.history_frame import describe_file, format_size
from geoclima.ui.messages import MessageType, WorkerMessage
from geoclima.ui.widgets.exceptions import InputValidationError
from geoclima.weather.domain.models import Station
from geoclima.weather.infrastructure.station_catalog import CatalogResult, CatalogSource
from tests.conftest import FakeKeyring

STATIONS = [
    Station(code="A565", name="BAMBUI", state="MG", status="Operante"),
    Station(code="A521", name="BELO HORIZONTE - PAMPULHA", state="MG", status="Operante"),
    Station(code="A999", name="QUEBRADA", state="MG", status="Pane"),
    Station(code="A422", name="ABROLHOS", state="BA", status="Operante"),
]


class FakeCatalog:
    def load(self, force_refresh=False):
        return CatalogResult(STATIONS, CatalogSource.STALE_CACHE)


def pump(window, until, timeout=5.0):
    """Runs the Tk loop until the condition holds (background threads report through the queue)."""
    deadline = time.monotonic() + timeout
    while not until():
        assert time.monotonic() < deadline, "timed out waiting for the window"
        window.update()
        window.process_queue()


class FakeThread:
    """Captures the worker instead of running it."""

    started: ClassVar[dict] = {}

    def __init__(self, target, args, daemon):
        FakeThread.started = {"target": target, "args": args}

    def start(self):
        FakeThread.started["running"] = True


KEYRING = FakeKeyring()


@pytest.fixture(scope="module")
def window(tmp_path_factory):
    # One window per module: creating a Tk root per test fails intermittently on Windows
    # ("Can't find a usable init.tcl").
    try:
        window = app_module.WeatherApp(
            output_dir=tmp_path_factory.mktemp("output"),
            catalog=FakeCatalog(),
            token_store=TokenStore(KEYRING),
            preferences_path=tmp_path_factory.mktemp("appdata") / "preferences.json",
        )
    except tkinter.TclError as e:
        pytest.skip(f"Tk unavailable: {e}")
    window.withdraw()
    pump(window, lambda: window.station_selector.rows)
    yield window
    window.destroy()


@pytest.fixture
def app(window):
    """The shared window, with the form, log, button and history reset to their initial state."""
    form = window.input_frame
    fill(form.token_input.entry, "")
    fill(form.initial_date_input.entry, (date.today() - timedelta(days=1)).isoformat())
    fill(form.final_date_input.entry, "")
    window.log_frame.reset()
    window.progress_frame.reset()
    window.action_frame.set_running(False)
    window.current_job = None
    window.input_frame.remember_token.deselect()
    window.export_options.set_values(ExportFormat.CSV, ExportMode.PER_DAY)
    window.station_selector.search("")
    window.station_selector.show_state("MG")
    for path in window.output_dir.iterdir():
        path.unlink()
    window.history_frame.populate_history()
    return window


def fill(entry, value):
    entry.delete(0, "end")
    if value:
        entry.insert(0, value)


def test_preferences_and_saved_token_are_restored_on_startup(window, tmp_path):
    # A second window is safe here: the shared one already initialized Tcl in this process.
    Preferences(export_format="EXCEL", export_mode="SINGLE_FILE", remember_token=True).save(tmp_path / "p.json")
    keyring = FakeKeyring()
    keyring.set_password("Geoclima", "inmet-token", "saved-token")

    other = app_module.WeatherApp(
        output_dir=tmp_path,
        catalog=FakeCatalog(),
        token_store=TokenStore(keyring),
        preferences_path=tmp_path / "p.json",
    )
    try:
        assert other.input_frame.token_input.get() == "saved-token"
        assert other.input_frame.remember_token.get() == 1
        assert other.export_options.export_format is ExportFormat.EXCEL
        assert other.export_options.mode is ExportMode.SINGLE_FILE
    finally:
        other.destroy()


def test_initial_date_defaults_to_yesterday(app):
    assert app.input_frame.initial_date_input.get() == (date.today() - timedelta(days=1)).isoformat()


def test_form_returns_typed_values(app):
    fill(app.input_frame.token_input.entry, " my-token ")
    fill(app.input_frame.initial_date_input.entry, "2025-08-28")
    fill(app.input_frame.final_date_input.entry, "2025-08-30")

    assert app.input_frame.get_values() == ("my-token", date(2025, 8, 28), date(2025, 8, 30))


def test_form_rejects_inverted_range(app):
    fill(app.input_frame.token_input.entry, "tk")
    fill(app.input_frame.initial_date_input.entry, "2025-08-30")
    fill(app.input_frame.final_date_input.entry, "2025-08-28")

    with pytest.raises(InputValidationError):
        app.input_frame.get_values()


def test_invalid_input_shows_warning_and_starts_nothing(app, monkeypatch):
    warnings = []
    monkeypatch.setattr(app_module.messagebox, "showwarning", lambda title, msg: warnings.append(msg))
    monkeypatch.setattr(app_module.threading, "Thread", lambda **kw: pytest.fail("worker must not start"))

    app.start_task()  # token is empty

    assert warnings == ["O campo de Token não pode estar vazio."]


def start(app, monkeypatch, token="tk"):
    monkeypatch.setattr(app_module.threading, "Thread", FakeThread)
    fill(app.input_frame.token_input.entry, token)
    app.start_task()
    return FakeThread.started


def test_start_task_builds_the_job_and_turns_the_button_into_cancel(app, monkeypatch):
    app.export_options.set_values(ExportFormat.EXCEL, ExportMode.SINGLE_FILE)

    started = start(app, monkeypatch)

    job, queue = started["args"]
    assert started["running"]
    assert queue is app.comm_queue
    assert (job.token, job.output_dir) == ("tk", app.output_dir)
    assert [s.code for s in job.stations] == ["A565", "A521"]
    assert (job.export_format, job.export_mode) == (ExportFormat.EXCEL, ExportMode.SINGLE_FILE)
    assert app.action_frame.start_button.cget("text") == CANCEL_TEXT


def test_cancel_sets_the_job_event(app, monkeypatch):
    job, _ = start(app, monkeypatch)["args"]

    app.action_frame.on_click()  # the same button now cancels

    assert job.cancel_event.is_set()
    assert app.action_frame.start_button.cget("state") == "disabled"


def test_remember_token_saves_it_in_the_vault_and_preferences(app, monkeypatch):
    app.input_frame.remember_token.select()

    start(app, monkeypatch, token="new-token")

    assert KEYRING.get_password("Geoclima", "inmet-token") == "new-token"
    assert Preferences.load(app.preferences_path).remember_token


def test_unchecking_remember_token_removes_it_from_the_vault(app, monkeypatch):
    KEYRING.set_password("Geoclima", "inmet-token", "old")
    app.preferences.remember_token = True

    start(app, monkeypatch)

    assert KEYRING.get_password("Geoclima", "inmet-token") is None
    assert not Preferences.load(app.preferences_path).remember_token


def test_calendar_popup_fills_the_date(app):
    popup = app.input_frame.final_date_input.open_calendar()
    try:
        popup.select(date(2025, 8, 30))
    finally:
        if popup.winfo_exists():
            popup.destroy()

    assert app.input_frame.final_date_input.get() == "2025-08-30"
    app.input_frame.final_date_input.clear_button.invoke()
    assert app.input_frame.final_date_input.get() == ""


def test_requires_at_least_one_station(app, monkeypatch):
    warnings = []
    monkeypatch.setattr(app_module.messagebox, "showwarning", lambda title, msg: warnings.append(msg))
    fill(app.input_frame.token_input.entry, "tk")
    app.station_selector.set_visible(False)

    app.start_task()

    assert warnings == ["Selecione pelo menos uma estação."]


def test_station_selector_defaults_to_operational_stations_of_mg(app):
    selector = app.station_selector

    assert selector.current_state == "MG"
    assert [s.code for s in selector.selected_stations()] == ["A565", "A521"]
    assert selector.count_label.cget("text") == "2 de 3 selecionadas"
    assert "catálogo salvo" in selector.note_label.cget("text")


def test_station_selector_search_and_bulk_selection(app):
    selector = app.station_selector

    selector.search("belo")
    selector.set_visible(False)
    selector.search("")

    assert [s.code for s in selector.selected_stations()] == ["A565"]


def test_station_selector_switches_state(app):
    app.station_selector.show_state("BA")

    assert [s.code for s in app.station_selector.selected_stations()] == ["A422"]


def test_worker_messages_update_the_window(app):
    app.action_frame.set_running(True)
    (app.output_dir / "2025_08_28.csv").write_text("x")

    for message in [
        WorkerMessage(MessageType.PROGRESS_START, 4),
        WorkerMessage(MessageType.PROGRESS_STEP, 1),
        WorkerMessage(MessageType.LOG, "Dados recebidos para: BAMBUI"),
        WorkerMessage(MessageType.TASK_CANCELLED, "cancelada"),
        WorkerMessage(MessageType.TASK_DONE, "pronto"),
        WorkerMessage(MessageType.TASK_FINISHED),
    ]:
        app.comm_queue.put(message)
    app.process_queue()

    assert app.progress_frame.progress_bar.get() == pytest.approx(0.25)
    assert app.progress_frame.status_label.cget("text").startswith("1/4 estações · ~")
    log = app.log_frame.log_text.get("1.0", "end")
    assert "AVISO: cancelada" in log
    assert "INFO: Dados recebidos para: BAMBUI" in log
    assert "SUCESSO: pronto" in log
    assert app.action_frame.start_button.cget("text") == START_TEXT
    assert history_files(app) == ["2025_08_28.csv"]


def history_files(app):
    return [row.path.name for row in app.history_frame.scrollable_frame.winfo_children() if hasattr(row, "path")]


def row_buttons(app, name):
    (row,) = [
        r
        for r in app.history_frame.scrollable_frame.winfo_children()
        if getattr(r, "path", None) and r.path.name == name
    ]
    return {w.cget("text"): w for w in row.winfo_children() if isinstance(w, customtkinter.CTkButton)}


def test_empty_history_shows_placeholder(app):
    labels = [w.cget("text") for w in app.history_frame.scrollable_frame.winfo_children()]

    assert labels == ["Nenhum arquivo encontrado."]
    assert app.history_frame.summary_label.cget("text").startswith("0 arquivo(s)")


def test_history_lists_exports_newest_first_with_details(app):
    old, new = app.output_dir / "MG_2025_08_28.csv", app.output_dir / "MG_2025_08_29.xlsx"
    old.write_text("x" * 2048)
    new.write_bytes(b"x")
    os.utime(old, (1_700_000_000, 1_700_000_000))
    (app.output_dir / "notes.txt").write_text("ignored")

    app.history_frame.populate_history()

    assert history_files(app) == ["MG_2025_08_29.xlsx", "MG_2025_08_28.csv"]
    assert describe_file(old).startswith("CSV · 2.0 KB · ")
    assert app.history_frame.summary_label.cget("text").startswith("2 arquivo(s)")


def test_history_row_actions(app, monkeypatch):
    path = app.output_dir / "MG_2025_08_28.csv"
    path.write_text("x")
    opened, popen = [], []
    monkeypatch.setattr(history_module.os, "startfile", opened.append, raising=False)
    monkeypatch.setattr(history_module.subprocess, "Popen", popen.append)
    app.history_frame.populate_history()

    buttons = row_buttons(app, path.name)
    buttons["Abrir"].invoke()
    buttons["Mostrar na pasta"].invoke()

    assert opened == [path]
    assert popen == [["explorer", "/select,", str(path)]]


@pytest.mark.parametrize(("size", "text"), [(10, "10 B"), (1536, "1.5 KB"), (3 * 1024 * 1024, "3.0 MB")])
def test_format_size(size, text):
    assert format_size(size) == text
