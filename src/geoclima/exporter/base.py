from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from geoclima.settings import OUTPUT_DIR
from geoclima.weather.domain.models import WeatherData

# Domain field -> column header shown to the user, in output order.
COLUMN_LABELS: dict[str, str] = {
    "measurement_date": "Data",
    "state": "UF",
    "station_code": "Código",
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
    """Writes records to one file. Subclasses only choose the format."""

    extension: str

    def __init__(
        self, records: list[WeatherData], file_stem: str, sheet_name: str, output_dir: Path = OUTPUT_DIR
    ) -> None:
        self.records = records
        self.file_stem = file_stem
        self.sheet_name = sheet_name
        self.output_dir = output_dir

    def export(self) -> Path:
        """Writes the file and returns its path."""
        path = self.get_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write(self.to_dataframe(), path)
        return path

    def get_file_path(self) -> Path:
        return self.output_dir / f"{self.file_stem}.{self.extension}"

    def to_dataframe(self) -> pd.DataFrame:
        ordered = sorted(self.records, key=lambda r: (r.measurement_date, r.station_name))
        rows = [record.model_dump(include=set(COLUMN_LABELS)) for record in ordered]
        return pd.DataFrame(rows, columns=list(COLUMN_LABELS)).rename(columns=COLUMN_LABELS)

    @abstractmethod
    def _write(self, df: pd.DataFrame, path: Path) -> None: ...
