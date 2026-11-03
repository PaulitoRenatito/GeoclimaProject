"""
Map tile downloads that follow the OpenStreetMap tile usage policy
(https://operations.osmfoundation.org/policies/tiles/): an identifying User-Agent and a local cache.

tkintermapview hardcodes `requests.get(url, headers={"User-Agent": "TkinterMapView"})`, a User-Agent
OSM blocks. install() swaps the `requests` name inside tkintermapview for a TileFetcher.
"""

import hashlib
import io
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from geoclima import __version__
from geoclima.settings import APP_DATA_DIR

logger = logging.getLogger(__name__)

USER_AGENT = f"Geoclima/{__version__} (+https://github.com/PaulitoRenatito/GeoclimaProject)"
CACHE_DIR = APP_DATA_DIR / "tiles"
CACHE_TTL_SECONDS = 30 * 24 * 60 * 60
TIMEOUT = (5, 15)


@dataclass
class TileResponse:
    """The only part of a requests.Response tkintermapview reads."""

    raw: io.BytesIO


class TileFetcher:
    # tkintermapview's handlers say `except requests.exceptions.ConnectionError`: keep that name valid.
    exceptions = requests.exceptions

    def __init__(self, cache_dir: Path = CACHE_DIR, session: requests.Session | None = None) -> None:
        self.cache_dir = cache_dir
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def get(self, url: str, **_ignored: object) -> TileResponse:
        path = self.cache_dir / f"{hashlib.sha1(url.encode()).hexdigest()}.png"
        if path.exists() and time.time() - path.stat().st_mtime < CACHE_TTL_SECONDS:
            return TileResponse(io.BytesIO(path.read_bytes()))

        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()  # tkintermapview catches errors and shows an empty tile
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
        except OSError:
            logger.warning("Could not cache map tile", exc_info=True)
        return TileResponse(io.BytesIO(response.content))


def install(fetcher: TileFetcher | None = None) -> None:
    from tkintermapview import map_widget

    map_widget.requests = fetcher or TileFetcher()
