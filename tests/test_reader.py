from datetime import date

import pytest

from geoclima.exporter.reader import ExportReadError, read_export
from geoclima.exporter.service import ExportFormat, ExportMode, export_records
from tests.conftest import make_record

DAY1, DAY2 = date(2025, 8, 28), date(2025, 8, 29)


@pytest.mark.parametrize("export_format", list(ExportFormat))
def test_round_trip(tmp_path, export_format):
    records = [make_record(DAY1), make_record(DAY2, "A521", "BELO HORIZONTE")]
    records[1] = records[1].model_copy(update={"precipitation": None})
    (path,) = export_records(records, export_format, ExportMode.SINGLE_FILE, tmp_path)

    loaded = read_export(path)

    assert [(r.measurement_date, r.station_code, r.state) for r in loaded] == [
        (DAY1, "A565", "MG"),
        (DAY2, "A521", "MG"),
    ]
    assert loaded[0].temp_avg == pytest.approx(20.7)
    assert loaded[1].precipitation is None


def test_reads_legacy_exports_without_date_and_code_columns(tmp_path):
    path = tmp_path / "2025_08_28.csv"
    path.write_text(
        "Nome da Estação,Temp. Mínima (°C),Temp. Máxima (°C),Temp. Média (°C),"
        "Umidade Minima (%),Umidade Média (%),Precipitação (mm),Vento (m/s)\n"
        "BAMBUI,11.7,31.2,20.7,29.0,63.4,0.0,1.2\n",
        encoding="utf-8-sig",
    )

    (record,) = read_export(path)

    assert (record.measurement_date, record.station_code, record.station_name) == (DAY1, "BAMBUI", "BAMBUI")
    assert record.temp_max == pytest.approx(31.2)


@pytest.mark.parametrize(("name", "content"), [("other.csv", "a,b\n1,2\n"), ("broken.xlsx", "not excel")])
def test_rejects_files_that_are_not_exports(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content)

    with pytest.raises(ExportReadError):
        read_export(path)


def test_rejects_export_without_any_date(tmp_path):
    path = tmp_path / "sem_data.csv"
    path.write_text("Nome da Estação,Temp. Máxima (°C)\nBAMBUI,31\n", encoding="utf-8-sig")

    with pytest.raises(ExportReadError, match="data"):
        read_export(path)
