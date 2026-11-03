"""Turns collected records into files, following the export options chosen in the UI."""

from collections import defaultdict
from datetime import date
from enum import Enum
from pathlib import Path

from geoclima.exporter.base import Exporter
from geoclima.exporter.csv_exporter import CsvExporter
from geoclima.exporter.excel_exporter import ExcelExporter
from geoclima.settings import OUTPUT_DIR
from geoclima.weather.domain.models import WeatherData


class ExportFormat(Enum):
    CSV = "CSV"
    EXCEL = "Excel"

    @property
    def exporter_class(self) -> type[Exporter]:
        return CsvExporter if self is ExportFormat.CSV else ExcelExporter


class ExportMode(Enum):
    PER_DAY = "Um arquivo por dia"
    SINGLE_FILE = "Arquivo único"


def export_records(
    records: list[WeatherData],
    export_format: ExportFormat = ExportFormat.CSV,
    mode: ExportMode = ExportMode.PER_DAY,
    output_dir: Path = OUTPUT_DIR,
) -> list[Path]:
    """Writes the files and returns their paths. Names start with the state(s), e.g. MG_2025_08_28.csv."""
    if not records:
        return []

    prefix = "-".join(sorted({record.state for record in records}))
    exporter_class = export_format.exporter_class

    if mode is ExportMode.SINGLE_FILE:
        days = sorted({record.measurement_date for record in records})
        first, last = days[0], days[-1]
        stem, sheet = _day_stem(first), first.isoformat()
        if first != last:
            stem, sheet = f"{stem}_a_{_day_stem(last)}", f"{first.isoformat()} a {last.isoformat()}"
        return [exporter_class(records, f"{prefix}_{stem}", sheet, output_dir).export()]

    records_by_day: dict[date, list[WeatherData]] = defaultdict(list)
    for record in records:
        records_by_day[record.measurement_date].append(record)

    return [
        exporter_class(day_records, f"{prefix}_{_day_stem(day)}", day.isoformat(), output_dir).export()
        for day, day_records in sorted(records_by_day.items())
    ]


def _day_stem(day: date) -> str:
    return day.strftime("%Y_%m_%d")
