from pathlib import Path

import pandas as pd

from geoclima.exporter.base import Exporter


class CsvExporter(Exporter):
    extension = "csv"

    def _write(self, df: pd.DataFrame, path: Path) -> None:
        # utf-8-sig adds a BOM so Excel opens accented headers correctly.
        df.to_csv(path, index=False, sep=",", encoding="utf-8-sig")
