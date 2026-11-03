"""User choices remembered between sessions (never the token: that lives in the credential vault)."""

import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from geoclima.exporter.service import ExportFormat, ExportMode
from geoclima.settings import APP_DATA_DIR

logger = logging.getLogger(__name__)

PREFERENCES_PATH = APP_DATA_DIR / "preferences.json"


@dataclass
class Preferences:
    state: str = "MG"
    export_format: str = ExportFormat.CSV.name
    export_mode: str = ExportMode.PER_DAY.name
    remember_token: bool = False

    @property
    def format(self) -> ExportFormat:
        return ExportFormat.__members__.get(self.export_format, ExportFormat.CSV)

    @property
    def mode(self) -> ExportMode:
        return ExportMode.__members__.get(self.export_mode, ExportMode.PER_DAY)

    @classmethod
    def load(cls, path: Path = PREFERENCES_PATH) -> "Preferences":
        """Returns the saved preferences; unknown keys are ignored and a broken file means defaults."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            known = {f.name for f in fields(cls)}
            return cls(**{key: value for key, value in data.items() if key in known})
        except FileNotFoundError:
            return cls()
        except (OSError, ValueError, TypeError, AttributeError):
            logger.warning("Ignoring unreadable preferences file %s", path, exc_info=True)
            return cls()

    def save(self, path: Path = PREFERENCES_PATH) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError:
            logger.warning("Could not save preferences", exc_info=True)
