from datetime import date

import openpyxl
import pandas as pd
import pytest

from geoclima.exporter.base import COLUMN_LABELS
from geoclima.exporter.csv_exporter import CsvExporter
from geoclima.exporter.excel_exporter import ExcelExporter
from geoclima.exporter.service import ExportFormat, ExportMode, export_records
from tests.conftest import make_record

DAY1, DAY2, DAY3 = date(2025, 8, 28), date(2025, 8, 29), date(2025, 8, 30)


@pytest.fixture
def records():
    return [make_record(DAY1, "A565", "BAMBUI"), make_record(DAY1, "A521", "BELO HORIZONTE - PAMPULHA")]


def test_csv_export_writes_labeled_columns_sorted_by_date_and_station(tmp_path, records):
    path = CsvExporter(list(reversed(records)), "MG_2025_08_28", "2025-08-28", tmp_path).export()

    assert path == tmp_path / "MG_2025_08_28.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    assert list(df.columns) == list(COLUMN_LABELS.values())
    assert df["Nome da Estação"].tolist() == ["BAMBUI", "BELO HORIZONTE - PAMPULHA"]
    assert df["Data"].tolist() == ["2025-08-28", "2025-08-28"]
    assert df["Código"].tolist() == ["A565", "A521"]
    assert df["Temp. Média (°C)"].tolist() == [20.7, 20.7]


def test_csv_starts_with_bom_so_excel_reads_accents(tmp_path, records):
    path = CsvExporter(records, "x", "x", tmp_path).export()

    assert path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_excel_export_sheet_name_widths_and_frozen_header(tmp_path, records):
    path = ExcelExporter(records, "x", "2025-08-28", tmp_path).export()

    sheet = openpyxl.load_workbook(path)["2025-08-28"]
    assert sheet.max_row == 3
    assert sheet.freeze_panes == "A2"
    assert sheet.column_dimensions["D"].width > len("Nome da Estação")


def test_excel_truncates_long_sheet_names(tmp_path, records):
    path = ExcelExporter(records, "x", "2025-08-28 a 2025-08-30 (muito longo)", tmp_path).export()

    assert openpyxl.load_workbook(path).sheetnames == ["2025-08-28 a 2025-08-30 (muito "]


def test_export_creates_missing_output_dir(tmp_path, records):
    assert CsvExporter(records, "x", "x", tmp_path / "nested" / "dir").export().exists()


def test_missing_values_are_left_blank(tmp_path):
    record = make_record(DAY1).model_copy(update={"precipitation": None})

    df = pd.read_csv(CsvExporter([record], "x", "x", tmp_path).export(), encoding="utf-8-sig")

    assert df["Precipitação (mm)"].isna().all()


def period_records():
    return [make_record(day, code) for day in (DAY3, DAY1, DAY2) for code in ("A565", "A521")]


def test_service_exports_one_file_per_day_prefixed_by_state(tmp_path):
    paths = export_records(period_records(), ExportFormat.CSV, ExportMode.PER_DAY, tmp_path)

    assert [p.name for p in paths] == ["MG_2025_08_28.csv", "MG_2025_08_29.csv", "MG_2025_08_30.csv"]
    assert all(len(pd.read_csv(p, encoding="utf-8-sig")) == 2 for p in paths)


def test_service_exports_single_file_for_the_period(tmp_path):
    (path,) = export_records(period_records(), ExportFormat.EXCEL, ExportMode.SINGLE_FILE, tmp_path)

    assert path.name == "MG_2025_08_28_a_2025_08_30.xlsx"
    workbook = openpyxl.load_workbook(path)
    assert workbook.sheetnames == ["2025-08-28 a 2025-08-30"]
    assert workbook.active.max_row == 7


def test_single_file_of_one_day_uses_the_day_name(tmp_path, records):
    (path,) = export_records(records, ExportFormat.CSV, ExportMode.SINGLE_FILE, tmp_path)

    assert path.name == "MG_2025_08_28.csv"


def test_service_with_several_states_and_no_records(tmp_path):
    bahia = make_record(DAY1, "A422", "ABROLHOS").model_copy(update={"state": "BA"})

    (path,) = export_records([bahia, make_record(DAY1)], output_dir=tmp_path)

    assert path.name == "BA-MG_2025_08_28.csv"
    assert export_records([], output_dir=tmp_path) == []
