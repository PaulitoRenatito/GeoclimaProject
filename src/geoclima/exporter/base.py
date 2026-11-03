from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path

import pandas as pd

from geoclima.settings import OUTPUT_DIR
from geoclima.weather.domain.models import WeatherData

# Domain field -> column header shown to the user, in output order.
COLUMN_LABELS: dict[str, str] = {
    "station_name": "Nome da Estação",
    "temp_min": "Temp. Mínima (°C)",
    "temp_max": "Temp. Máxima (°C)",
    "temp_avg": "Temp. Média (°C)",
    "humidity_min": "Umidade Mínima (%)",
    "humidity_avg": "Umidade Média (%)",
    "precipitation": "Precipitação (mm)",
    "wind_speed_avg": "Vento (m/s)",
}


class Exporter(ABC):
    """
    Writes the records of one day to a file. Subclasses only choose the format.
    """

    extension: str

    def __init__(self, day: date, data: list[WeatherData], output_dir: Path = OUTPUT_DIR) -> None:
        self.day = day
        self.data = data
        self.output_dir = output_dir

    def export(self) -> Path:
        """Writes the file and returns its path."""
        path = self.get_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write(self.to_dataframe(), path)
        return path

    def get_file_path(self) -> Path:
        return self.output_dir / f"{self.day.strftime('%Y_%m_%d')}.{self.extension}"

    def to_dataframe(self) -> pd.DataFrame:
        rows = [record.model_dump(include=set(COLUMN_LABELS)) for record in self.data]
        return pd.DataFrame(rows, columns=list(COLUMN_LABELS)).rename(columns=COLUMN_LABELS)

    @abstractmethod
    def _write(self, df: pd.DataFrame, path: Path) -> None: ...
