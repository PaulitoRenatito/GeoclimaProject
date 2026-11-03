import os
from pathlib import Path

# Fixed location so the app writes to the same place no matter where it is launched from
# (a relative "output" folder lands next to wherever the user opened the .exe).
OUTPUT_DIR = Path.home() / "Documents" / "Geoclima"

# Internal app files (station catalog cache, preferences). Not meant to be opened by the user.
APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share") / "Geoclima"
