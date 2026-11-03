"""Smoke tests of the real Tk window. Skipped where no display is available."""

import time
import tkinter
from datetime import date, timedelta

import pytest

from geoclima.ui import app as app_module
from geoclima.ui.messages import MessageType, WorkerMessage
from geoclima.ui.widgets.exceptions import InputValidationError
from geoclima.weather.domain.models import Station
from geoclima.weather.infrastructure.station_catalog import CatalogResult, CatalogSource

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


@pytest.fixture(scope="module")
def window(tmp_path_factory):
    # One window per module: creating a Tk root per test fails intermittently on Windows
    # ("Can't find a usable init.tcl").
    try:
        window = app_module.WeatherApp(output_dir=tmp_path_factory.mktemp("output"), catalog=FakeCatalog())
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
    window.action_frame.set_button_state("normal")
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


def test_start_task_disables_button_and_starts_worker(app, monkeypatch):
    started = {}

    class FakeThread:
        def __init__(self, target, args, daemon):
            started.update(target=target, args=args)

        def start(self):
            started["running"] = True

    monkeypatch.setattr(app_module.threading, "Thread", FakeThread)
    fill(app.input_frame.token_input.entry, "tk")

    app.start_task()

    job, queue = started["args"]
    assert started["running"]
    assert queue is app.comm_queue
    assert (job.token, job.output_dir) == ("tk", app.output_dir)
    assert [s.code for s in job.stations] == ["A565", "A521"]
    assert app.action_frame.start_button.cget("state") == "disabled"


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
    app.action_frame.set_button_state("disabled")
    (app.output_dir / "2025_08_28.csv").write_text("x")

    for message in [
        WorkerMessage(MessageType.PROGRESS_START, 4),
        WorkerMessage(MessageType.PROGRESS_STEP, 1),
        WorkerMessage(MessageType.LOG, "Dados recebidos para: BAMBUI"),
        WorkerMessage(MessageType.TASK_DONE, "pronto"),
        WorkerMessage(MessageType.TASK_FINISHED),
    ]:
        app.comm_queue.put(message)
    app.process_queue()

    assert app.progress_frame.progress_bar.get() == pytest.approx(0.25)
    log = app.log_frame.log_text.get("1.0", "end")
    assert "INFO: Dados recebidos para: BAMBUI" in log
    assert "SUCESSO: pronto" in log
    assert app.action_frame.start_button.cget("state") == "normal"
    history = [w.cget("text") for w in app.history_frame.scrollable_frame.winfo_children()]
    assert history == ["2025_08_28.csv"]


def test_empty_history_shows_placeholder(app):
    labels = [w.cget("text") for w in app.history_frame.scrollable_frame.winfo_children()]

    assert labels == ["Nenhum arquivo encontrado."]
