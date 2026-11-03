import json
import os

import pytest
import responses

from geoclima.weather.domain.models import Station
from geoclima.weather.infrastructure import inmet_client
from geoclima.weather.infrastructure.exceptions import StationCatalogError
from geoclima.weather.infrastructure.station_catalog import (
    CatalogSource,
    StationCatalog,
    built_in_stations,
    states_of,
)
from geoclima.weather.infrastructure.stations import MG_STATIONS

RAW_STATIONS = [
    {
        "CD_ESTACAO": "A422",
        "DC_NOME": "ABROLHOS",
        "SG_ESTADO": "BA",
        "CD_SITUACAO": "Pane",
        "VL_LATITUDE": "-17.96305555",
        "VL_LONGITUDE": "-38.70333333",
        "TP_ESTACAO": "Automatica",
    },
    {
        "CD_ESTACAO": "A565",
        "DC_NOME": "BAMBUI",
        "SG_ESTADO": "MG",
        "CD_SITUACAO": "Operante",
        "VL_LATITUDE": "-20.03138888",
        "VL_LONGITUDE": "-46.00888888",
    },
]
STATIONS = [Station.model_validate(raw) for raw in RAW_STATIONS]
NOW = 1_800_000_000.0


class FakeFetch:
    def __init__(self, result=None, error=False):
        self.result = result if result is not None else STATIONS
        self.error = error
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.error:
            raise StationCatalogError("offline")
        return self.result


def catalog(tmp_path, fetch, age_seconds=None):
    cache = tmp_path / "stations.json"
    if age_seconds is not None:
        cache.write_text(json.dumps(RAW_STATIONS[:1]))
        os.utime(cache, (NOW - age_seconds, NOW - age_seconds))
    return StationCatalog(cache_path=cache, fetch=fetch, ttl_seconds=3600, clock=lambda: NOW)


def test_station_model():
    abrolhos, bambui = STATIONS

    assert (abrolhos.code, abrolhos.state, abrolhos.latitude) == ("A422", "BA", pytest.approx(-17.96305555))
    assert not abrolhos.is_operational
    assert bambui.is_operational
    assert Station(code="X", name="X", state="MG").is_operational


def test_downloads_and_caches_when_there_is_no_cache(tmp_path):
    fetch = FakeFetch()

    result = catalog(tmp_path, fetch).load()

    assert result.source is CatalogSource.API
    assert [s.code for s in result.stations] == ["A422", "A565"]
    cached = json.loads((tmp_path / "stations.json").read_text())
    assert cached[1]["CD_ESTACAO"] == "A565"


def test_fresh_cache_skips_the_api(tmp_path):
    fetch = FakeFetch()

    result = catalog(tmp_path, fetch, age_seconds=60).load()

    assert result.source is CatalogSource.CACHE
    assert [s.code for s in result.stations] == ["A422"]
    assert fetch.calls == 0


def test_expired_cache_is_refreshed(tmp_path):
    result = catalog(tmp_path, FakeFetch(), age_seconds=7200).load()

    assert result.source is CatalogSource.API
    assert len(result.stations) == 2


def test_force_refresh_ignores_fresh_cache(tmp_path):
    fetch = FakeFetch()

    catalog(tmp_path, fetch, age_seconds=60).load(force_refresh=True)

    assert fetch.calls == 1


def test_offline_uses_stale_cache(tmp_path):
    result = catalog(tmp_path, FakeFetch(error=True), age_seconds=7200).load()

    assert result.source is CatalogSource.STALE_CACHE
    assert [s.code for s in result.stations] == ["A422"]


def test_offline_without_cache_uses_built_in_list(tmp_path):
    result = catalog(tmp_path, FakeFetch(error=True)).load()

    assert result.source is CatalogSource.BUILT_IN
    assert len(result.stations) == len(MG_STATIONS)


def test_corrupt_cache_is_ignored(tmp_path):
    (tmp_path / "stations.json").write_text("not json")

    result = catalog(tmp_path, FakeFetch()).load()

    assert result.source is CatalogSource.API


def test_built_in_stations_and_states():
    stations = built_in_stations()

    assert {s.state for s in stations} == {"MG"}
    assert states_of(STATIONS) == ["BA", "MG"]


@responses.activate
def test_fetch_stations_parses_catalog():
    responses.get(f"{inmet_client.BASE_URL}/estacoes/T", json=RAW_STATIONS)

    assert [s.name for s in inmet_client.fetch_stations()] == ["ABROLHOS", "BAMBUI"]


@responses.activate
@pytest.mark.parametrize("kwargs", [{"status": 404}, {"body": "<html>"}])
def test_fetch_stations_errors(kwargs):
    responses.get(f"{inmet_client.BASE_URL}/estacoes/T", **kwargs)

    with pytest.raises(StationCatalogError):
        inmet_client.fetch_stations()
