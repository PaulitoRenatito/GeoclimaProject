"""
Map tile downloads that follow the OpenStreetMap tile usage policy
(https://operations.osmfoundation.org/policies/tiles/): an identifying User-Agent and a local cache.
"""

import hashlib
import logging
import time
from pathlib import Path

import requests

from geoclima import __version__
from geoclima.settings import APP_DATA_DIR

logger = logging.getLogger(__name__)

USER_AGENT = f"Geoclima/{__version__} (+https://github.com/PaulitoRenatito/GeoclimaProject)"
CACHE_DIR = APP_DATA_DIR / "tiles"
CACHE_TTL_SECONDS = 30 * 24 * 60 * 60
TIMEOUT = (5, 15)


class TileFetcher:
    def __init__(self, cache_dir: Path = CACHE_DIR, session: requests.Session | None = None) -> None:
        self.cache_dir = cache_dir
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def fetch(self, url: str) -> bytes:
        """The tile image, from the local cache when fresh. Raises on HTTP errors."""
        path = self.cache_dir / f"{hashlib.sha1(url.encode()).hexdigest()}.png"
        if path.exists() and time.time() - path.stat().st_mtime < CACHE_TTL_SECONDS:
            return path.read_bytes()

        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
        except OSError:
            logger.warning("Could not cache map tile", exc_info=True)
        return response.content
