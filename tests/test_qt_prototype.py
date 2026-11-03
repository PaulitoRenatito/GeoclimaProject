"""Smoke tests of the PySide6 prototype. Skipped unless the optional group is installed (poetry install --with qt)."""

import os
from datetime import date

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QMessageBox

from geoclima.exporter.service import ExportFormat, ExportMode, export_records
from geoclima.qt import charts_page
from geoclima.qt.__main__ import main
from geoclima.qt.main_window import MainWindow
from tests.conftest import make_record

DAY1, DAY2 = date(2025, 8, 28), date(2025, 8, 29)


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def page(qapp, tmp_path):
    window = MainWindow()
    records = [
        make_record(DAY1, "A565", "BAMBUI").model_copy(update={"temp_max": 30.0}),
        make_record(DAY2, "A565", "BAMBUI").model_copy(update={"temp_max": 34.0}),
        make_record(DAY1, "A521", "BELO HORIZONTE").model_copy(update={"temp_max": 28.0}),
    ]
    (path,) = export_records(records, ExportFormat.EXCEL, ExportMode.SINGLE_FILE, tmp_path)
    window.charts.load_file(path)
    yield window.charts
    window.close()


def test_loads_file_into_cards_ranking_and_station_menu(page):
    assert page.subtitle.text().endswith("2 estação(ões) · 28/08/2025 a 29/08/2025 · 3 registro(s)")
    assert page.cards.count() == 4
    assert [page.ranking_model.item(row).text() for row in range(2)] == ["BAMBUI", "BELO HORIZONTE"]
    assert page.ranking_model.item(0, 1).text() == "32.0"
    assert [page.station_combo.itemText(i) for i in range(3)] == ["Média das estações", "BAMBUI", "BELO HORIZONTE"]
    assert not page.station_combo.isEnabled()


def test_bar_tooltip(page):
    # Bars are drawn bottom-up: index 0 is the lowest value.
    assert page.tooltip_at(QPointF(10, 0)) == "<b>BELO HORIZONTE</b> (A521)<br>28.0 °C"
    assert page.tooltip_at(QPointF(10, 1)).startswith("<b>BAMBUI</b>")
    assert page.tooltip_at(QPointF(10, 5)) is None


def test_station_evolution_with_average_and_tooltip(page):
    page.show_station("BAMBUI")

    assert page.over_time
    assert page.station_combo.isEnabled()
    assert page.ranking.selectionModel().selectedRows()[0].row() == 0
    assert page.tooltip_at(QPointF(0, 30)) == ("<b>28/08/2025</b><br>BAMBUI: 30.0 °C<br>Média das estações: 29.0 °C")
    assert page.tooltip_at(QPointF(1, 30)).endswith("Média das estações: 34.0 °C")


def test_rain_over_time_and_empty_state(page):
    page.metric_combo.setCurrentText("Precipitação acumulada")
    page.show_station("Média das estações")
    assert set(page.hover_series) == {"Média das estações"}

    page.set_records([], "")
    assert page.subtitle.text() == "Nenhum dado carregado"
    assert page.cards.count() == 0
    assert page.tooltip_at(QPointF(0, 0)) is None


def test_invalid_file_shows_error(page, tmp_path, monkeypatch):
    errors = []
    monkeypatch.setattr(QMessageBox, "critical", lambda parent, title, text: errors.append(text))
    path = tmp_path / "outro.csv"
    path.write_text("a,b\n1,2\n")

    page.load_file(path)

    assert "não parece ser um arquivo exportado" in errors[0]


def test_choose_file(page, monkeypatch):
    loaded = []
    monkeypatch.setattr(page, "load_file", loaded.append)
    monkeypatch.setattr(charts_page.QFileDialog, "getOpenFileName", lambda *a: ("C:/x/MG.csv", ""))
    page.choose_file()
    monkeypatch.setattr(charts_page.QFileDialog, "getOpenFileName", lambda *a: ("", ""))
    page.choose_file()

    assert [p.name for p in loaded] == ["MG.csv"]


def test_main_opens_the_window(qapp, monkeypatch, tmp_path):
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    assert main([]) == 0
