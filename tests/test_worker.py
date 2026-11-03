from datetime import date
from queue import Queue

import pytest

from geoclima.ui import worker
from geoclima.ui.messages import MessageType
from tests.conftest import make_record

DAY1, DAY2 = date(2025, 8, 28), date(2025, 8, 29)


def run(monkeypatch, tmp_path, result):
    def fake_collect(**kwargs):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(worker, "collect_weather_data", fake_collect)
    queue: Queue = Queue()
    worker.run_collection("tk", queue, DAY1, DAY2, output_dir=tmp_path)
    return [queue.get_nowait() for _ in range(queue.qsize())]


def types(messages):
    return [m.type for m in messages]


def test_exports_one_file_per_day(monkeypatch, tmp_path):
    messages = run(monkeypatch, tmp_path, [make_record(DAY2), make_record(DAY1), make_record(DAY1, "A521")])

    assert sorted(p.name for p in tmp_path.iterdir()) == ["2025_08_28.csv", "2025_08_29.csv"]
    assert types(messages)[-2:] == [MessageType.TASK_DONE, MessageType.TASK_FINISHED]


def test_no_data_reports_error(monkeypatch, tmp_path):
    messages = run(monkeypatch, tmp_path, [])

    assert types(messages) == [MessageType.TASK_ERROR, MessageType.TASK_FINISHED]
    assert not list(tmp_path.iterdir())


def test_unexpected_error_is_reported_and_task_still_finishes(monkeypatch, tmp_path):
    messages = run(monkeypatch, tmp_path, RuntimeError("disk full"))

    assert types(messages) == [MessageType.TASK_ERROR, MessageType.TASK_FINISHED]
    assert "disk full" in messages[0].payload


@pytest.mark.parametrize(
    ("records", "expected"),
    [
        ([make_record(DAY1)], "Dados recebidos para: BAMBUI"),
        ([], "Estação A1 sem dados no período."),
        (None, "Falha ao obter dados da estação: A1"),
    ],
)
def test_queue_listener_messages(records, expected):
    queue: Queue = Queue()

    worker.QueueListener(queue).on_station_result("A1", records)

    log, step = queue.get_nowait(), queue.get_nowait()
    assert (log.type, log.payload) == (MessageType.LOG, expected)
    assert (step.type, step.payload) == (MessageType.PROGRESS_STEP, 1)
