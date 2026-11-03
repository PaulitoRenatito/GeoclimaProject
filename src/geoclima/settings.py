from pathlib import Path

# Fixed location so the app writes to the same place no matter where it is launched from
# (a relative "output" folder lands next to wherever the user opened the .exe).
OUTPUT_DIR = Path.home() / "Documents" / "Geoclima"
