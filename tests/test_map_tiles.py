import os
import time

import pytest
import requests
import responses

from geoclima.ui import map_tiles
from geoclima.ui.map_tiles import USER_AGENT, TileFetcher

URL = "https://tile.openstreetmap.org/5/11/17.png"


@responses.activate
def test_downloads_with_identifying_user_agent_and_caches(tmp_path):
    responses.get(URL, body=b"PNG-1")
    fetcher = TileFetcher(cache_dir=tmp_path)

    first = fetcher.get(URL, stream=True, headers={"User-Agent": "TkinterMapView"})
    second = fetcher.get(URL)

    assert first.raw.read() == second.raw.read() == b"PNG-1"
    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["User-Agent"] == USER_AGENT
    assert "Geoclima/" in USER_AGENT


@responses.activate
def test_expired_cache_is_downloaded_again(tmp_path):
    responses.get(URL, body=b"PNG-1")
    responses.get(URL, body=b"PNG-2")
    fetcher = TileFetcher(cache_dir=tmp_path)
    fetcher.get(URL)
    (cached,) = tmp_path.iterdir()
    old = time.time() - map_tiles.CACHE_TTL_SECONDS - 10
    os.utime(cached, (old, old))

    assert fetcher.get(URL).raw.read() == b"PNG-2"


@responses.activate
def test_http_errors_raise_so_the_map_shows_an_empty_tile(tmp_path):
    responses.get(URL, status=403)

    with pytest.raises(requests.HTTPError):
        TileFetcher(cache_dir=tmp_path).get(URL)
    assert not list(tmp_path.iterdir())


def test_install_replaces_requests_inside_tkintermapview():
    from tkintermapview import map_widget

    original = map_widget.requests
    fetcher = TileFetcher()
    try:
        map_tiles.install(fetcher)
        assert map_widget.requests is fetcher
        # tkintermapview's own except clauses must keep resolving.
        assert map_widget.requests.exceptions.ConnectionError is requests.exceptions.ConnectionError
    finally:
        map_widget.requests = original
