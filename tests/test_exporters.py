from datetime import date

import pandas as pd
import pytest

from geoclima.exporter.base import COLUMN_LABELS
from geoclima.exporter.csv_exporter import CsvExporter
from geoclima.exporter.excel_exporter import ExcelExporter
from tests.conftest import make_record

DAY = date(2025, 8, 28)


@pytest.fixture
def records():
    return [make_record(DAY, "A565", "BAMBUI"), make_record(DAY, "A521", "BELO HORIZONTE - PAMPULHA")]


def test_csv_export_writes_labeled_columns(tmp_path, records):
    path = CsvExporter(DAY, records, output_dir=tmp_path).export()

    assert path == tmp_path / "2025_08_28.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    assert list(df.columns) == list(COLUMN_LABELS.values())
    assert df["Nome da Estação"].tolist() == ["BAMBUI", "BELO HORIZONTE - PAMPULHA"]
    assert df["Temp. Média (°C)"].tolist() == [20.7, 20.7]


def test_csv_starts_with_bom_so_excel_reads_accents(tmp_path, records):
    path = CsvExporter(DAY, records, output_dir=tmp_path).export()

    assert path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_excel_export_uses_date_as_sheet_name(tmp_path, records):
    path = ExcelExporter(DAY, records, output_dir=tmp_path).export()

    assert path.suffix == ".xlsx"
    sheets = pd.read_excel(path, sheet_name=None)
    assert list(sheets) == ["2025-08-28"]
    assert len(sheets["2025-08-28"]) == 2


def test_export_creates_missing_output_dir(tmp_path, records):
    output_dir = tmp_path / "nested" / "dir"

    assert CsvExporter(DAY, records, output_dir=output_dir).export().exists()


def test_missing_values_are_left_blank(tmp_path):
    record = make_record(DAY).model_copy(update={"precipitation": None})

    df = pd.read_csv(CsvExporter(DAY, [record], output_dir=tmp_path).export(), encoding="utf-8-sig")

    assert df["Precipitação (mm)"].isna().all()
