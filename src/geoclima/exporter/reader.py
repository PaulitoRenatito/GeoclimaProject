"""Reads files written by the exporters back into records, so past collections can be charted."""

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from geoclima.exporter.base import COLUMN_LABELS
from geoclima.weather.domain.models import WeatherData

LABEL_TO_FIELD = {label: field for field, label in COLUMN_LABELS.items()}
# Files exported before v0.2 have neither Data, UF nor Código columns: the date comes from the name.
LEGACY_NAME = re.compile(r"(?:(?P<state>[A-Z]{2})_)?(?P<date>\d{4}_\d{2}_\d{2})")


class ExportReadError(Exception):
    """Raised when a file is not a Geoclima export."""


def read_export(path: Path) -> list[WeatherData]:
    try:
        df = pd.read_excel(path) if path.suffix == ".xlsx" else pd.read_csv(path, encoding="utf-8-sig")
    except Exception as e:
        raise ExportReadError(f"Não foi possível ler '{path.name}': {e}") from e

    if "Nome da Estação" not in df.columns:
        raise ExportReadError(f"'{path.name}' não parece ser um arquivo exportado pelo Geoclima.")

    df = df.rename(columns=LABEL_TO_FIELD)
    df = df.astype(object).where(pd.notna(df), None)  # NaN -> None, so pydantic sees missing values
    legacy = LEGACY_NAME.match(path.stem)

    records = []
    for row in df.to_dict("records"):
        values: dict[str, Any] = {key: value for key, value in row.items() if key in COLUMN_LABELS}
        values["measurement_date"] = _parse_date(values.get("measurement_date"), legacy)
        values.setdefault("state", (legacy and legacy["state"]) or "")
        values.setdefault("station_code", values["station_name"])
        values["station_code"] = str(values["station_code"] or values["station_name"])
        values["state"] = str(values["state"] or "")
        records.append(WeatherData.model_validate(values))
    return records


def _parse_date(value: object, legacy: re.Match[str] | None) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value[:10])
    if legacy:
        return datetime.strptime(legacy["date"], "%Y_%m_%d").date()
    raise ExportReadError("O arquivo não informa a data das medições.")
