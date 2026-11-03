"""Station catalog with a local cache, so the app starts fast and keeps working offline."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from geoclima.settings import APP_DATA_DIR
from geoclima.weather.domain.models import Station
from geoclima.weather.infrastructure import inmet_client
from geoclima.weather.infrastructure.exceptions import StationCatalogError
from geoclima.weather.infrastructure.stations import MG_STATIONS

logger = logging.getLogger(__name__)

# The catalog rarely changes, and the INMET docs recommend caching it.
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

_station_list_adapter = TypeAdapter(list[Station])


class CatalogSource(Enum):
    CACHE = "cache"
    API = "api"
    STALE_CACHE = "stale_cache"  # API failed, cache older than the TTL used instead
    BUILT_IN = "built_in"  # API failed and no cache: bundled MG list, without coordinates


@dataclass(frozen=True)
class CatalogResult:
    stations: list[Station]
    source: CatalogSource


class StationCatalog:
    def __init__(
        self,
        cache_path: Path = APP_DATA_DIR / "stations.json",
        fetch: Callable[[], list[Station]] = inmet_client.fetch_stations,
        ttl_seconds: float = CACHE_TTL_SECONDS,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.cache_path = cache_path
        self.fetch = fetch
        self.ttl_seconds = ttl_seconds
        self.clock = clock

    def load(self, force_refresh: bool = False) -> CatalogResult:
        """Cache if fresh, else API (refreshing the cache), else any cache, else the built-in list."""
        cached = self._read_cache()
        if cached is not None and not force_refresh and self._cache_is_fresh():
            return CatalogResult(cached, CatalogSource.CACHE)

        try:
            stations = self.fetch()
        except StationCatalogError:
            logger.warning("Could not download the station catalog", exc_info=True)
        else:
            self._write_cache(stations)
            return CatalogResult(stations, CatalogSource.API)

        if cached is not None:
            return CatalogResult(cached, CatalogSource.STALE_CACHE)
        return CatalogResult(built_in_stations(), CatalogSource.BUILT_IN)

    def _cache_is_fresh(self) -> bool:
        return self.clock() - self.cache_path.stat().st_mtime < self.ttl_seconds

    def _read_cache(self) -> list[Station] | None:
        try:
            return _station_list_adapter.validate_json(self.cache_path.read_bytes())
        except FileNotFoundError:
            return None
        except (OSError, ValidationError):
            logger.warning("Ignoring unreadable station cache %s", self.cache_path, exc_info=True)
            return None

    def _write_cache(self, stations: list[Station]) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_bytes(_station_list_adapter.dump_json(stations, by_alias=True))
        except OSError:
            logger.warning("Could not write the station cache", exc_info=True)


def built_in_stations() -> list[Station]:
    return [Station(code=code, name=name, state="MG") for name, code in MG_STATIONS.items()]


def states_of(stations: list[Station]) -> list[str]:
    return sorted({station.state for station in stations})
