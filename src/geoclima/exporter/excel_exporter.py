from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter

from geoclima.exporter.base import Exporter

# Excel rejects sheet names longer than 31 characters.
MAX_SHEET_NAME = 31


class ExcelExporter(Exporter):
    extension = "xlsx"

    def _write(self, df: pd.DataFrame, path: Path) -> None:
        sheet_name = self.sheet_name[:MAX_SHEET_NAME]
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            sheet = writer.sheets[sheet_name]
            sheet.freeze_panes = "A2"
            for index, column in enumerate(df.columns, start=1):
                width = max([len(str(column)), *(len(str(value)) for value in df[column])])
                sheet.column_dimensions[get_column_letter(index)].width = width + 2
