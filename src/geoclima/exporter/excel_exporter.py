from pathlib import Path

import pandas as pd

from geoclima.exporter.base import Exporter


class ExcelExporter(Exporter):
    extension = "xlsx"

    def _write(self, df: pd.DataFrame, path: Path) -> None:
        df.to_excel(path, index=False, sheet_name=self.day.isoformat())
