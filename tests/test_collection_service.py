import threading
from datetime import date

import pytest

from geoclima.weather.application import collection_service
from geoclima.weather.application.collection_service import CollectionCancelled, collect_weather_data
from geoclima.weather.infrastructure.exceptions import StationDataError
from tests.conftest import make_record

DAY = date(2025, 8, 28)


class RecordingListener:
    def __init__(self):
        self.events = []

    def on_start(self, total):
        self.events.append(("start", total))

    def on_station_result(self, station_code, records):
        self.events.append((station_code, None if records is None else len(records)))


def fake_fetch(initial_date, final_date, station_code, token):
    if station_code == "FAIL":
        raise StationDataError("boom")
    if station_code == "EMPTY":
        return []
    return [make_record(initial_date, station_code), make_record(final_date, station_code)]


def collect(**kwargs):
    defaults = {"token": "tk", "initial_date": DAY, "fetch": fake_fetch, "request_interval": 0}
    return collect_weather_data(**(defaults | kwargs))


def test_collects_records_of_all_stations():
    records = collect(station_codes=["A1", "A2"])

    assert [r.station_code for r in records] == ["A1", "A1", "A2", "A2"]


def test_failing_station_is_skipped_and_reported():
    listener = RecordingListener()

    records = collect(station_codes=["A1", "FAIL", "EMPTY"], listener=listener)

    assert {r.station_code for r in records} == {"A1"}
    assert listener.events == [("start", 3), ("A1", 2), ("FAIL", None), ("EMPTY", 0)]


def test_final_date_defaults_to_initial_date():
    calls = []

    def spy(initial_date, final_date, station_code, token):
        calls.append((initial_date, final_date))
        return []

    collect(station_codes=["A1"], fetch=spy)

    assert calls == [(DAY, DAY)]


def test_waits_between_requests(monkeypatch):
    sleeps = []
    monkeypatch.setattr(collection_service.time, "sleep", sleeps.append)

    collect(station_codes=["A1", "A2"], request_interval=0.8)

    assert len(sleeps) == 2
    assert all(0 < s <= 0.8 for s in sleeps)


@pytest.mark.parametrize("interval", [0, -1])
def test_non_positive_interval_never_sleeps(monkeypatch, interval):
    monkeypatch.setattr(collection_service.time, "sleep", lambda s: pytest.fail("should not sleep"))

    collect(station_codes=["A1"], request_interval=interval)


def test_uses_mg_stations_by_default():
    codes = []

    collect(fetch=lambda i, f, code, t: codes.append(code) or [])

    assert codes == list(collection_service.MG_STATIONS.values())
    assert len(codes) == len(set(codes)), "station codes must be unique"


def test_cancel_stops_before_the_next_station():
    cancel = threading.Event()
    fetched = []

    def fetch_then_cancel(initial_date, final_date, station_code, token):
        fetched.append(station_code)
        cancel.set()
        return []

    with pytest.raises(CollectionCancelled):
        collect(station_codes=["A1", "A2", "A3"], fetch=fetch_then_cancel, cancel_event=cancel)

    assert fetched == ["A1"]


def test_cancel_interrupts_the_wait_between_requests(monkeypatch):
    monkeypatch.setattr(collection_service.time, "sleep", lambda s: pytest.fail("must wait on the event"))
    cancel = threading.Event()
    waits = []

    class RecordingEvent:
        def is_set(self):
            return cancel.is_set()

        def wait(self, timeout):
            waits.append(timeout)
            cancel.set()

    with pytest.raises(CollectionCancelled):
        collect(station_codes=["A1", "A2"], request_interval=60, cancel_event=RecordingEvent())

    assert len(waits) == 1
