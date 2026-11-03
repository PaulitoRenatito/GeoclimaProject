from datetime import date

import pytest
from PySide6.QtCore import QBuffer, QByteArray, QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QMouseEvent
from PySide6.QtWidgets import QPushButton

from geoclima.ui.pages.map import MapPage
from geoclima.ui.widgets.tile_map import (
    BRAZIL_CENTER,
    MAX_FIT_ZOOM,
    Marker,
    TileMap,
    fit_view,
    project,
    text_color_for,
    unproject,
)
from tests.conftest import make_record

BH = (-19.92, -43.94)
BAMBUI = (-20.03, -46.0)


def png_bytes(color="#3366CC") -> bytes:
    image = QImage(256, 256, QImage.Format.Format_RGB32)
    image.fill(QColor(color))
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(data.data())


class FakeFetch:
    def __init__(self, fail=False):
        self.urls = []
        self.fail = fail

    def __call__(self, url):
        self.urls.append(url)
        if self.fail:
            raise OSError("offline")
        return png_bytes()


@pytest.fixture
def tile_map(qtbot):
    widget = TileMap(FakeFetch())
    qtbot.addWidget(widget)
    widget.resize(800, 600)
    widget.show()
    qtbot.waitExposed(widget)
    return widget


# Projection ----------------------------------------------------------------


def test_project_known_points():
    assert project(0, 0, 0) == QPointF(128, 128)
    assert project(0, -180, 1).x() == pytest.approx(0)
    assert project(85.0511, 180, 1).y() == pytest.approx(0, abs=0.01)


@pytest.mark.parametrize("zoom", [3, 8, 14])
def test_unproject_inverts_project(zoom):
    lat, lon = unproject(project(*BH, zoom), zoom)
    assert (lat, lon) == (pytest.approx(BH[0]), pytest.approx(BH[1]))


def test_fit_view():
    assert fit_view([], 800, 600) == (BRAZIL_CENTER, 4)
    assert fit_view([BH], 800, 600) == (BH, MAX_FIT_ZOOM)

    (_lat, lon), zoom = fit_view([BH, BAMBUI], 800, 600)
    assert BAMBUI[1] < lon < BH[1]
    span = project(*BH, zoom).x() - project(*BAMBUI, zoom).x()
    assert span <= 800 - 120
    assert project(*BH, zoom + 1).x() - project(*BAMBUI, zoom + 1).x() > 800 - 120 or zoom == MAX_FIT_ZOOM


def test_text_color_contrasts_with_marker():
    assert text_color_for(QColor("#FFFFFF")) == QColor("#1E1E1E")
    assert text_color_for(QColor("#08306B")) == QColor("#FFFFFF")


# Widget --------------------------------------------------------------------


def test_tiles_are_downloaded_once_cached_in_grayscale(tile_map, qtbot):
    qtbot.waitUntil(lambda: len(tile_map.tiles) == len(tile_map.visible_tiles()))

    fetch = tile_map.fetch
    assert all(url.startswith("https://tile.openstreetmap.org/4/") for url in fetch.urls)
    assert len(fetch.urls) == len(set(fetch.urls))
    pixmap = next(iter(tile_map.tiles.values()))
    assert pixmap.toImage().isGrayscale()

    tile_map.repaint()
    assert len(fetch.urls) == len(tile_map.tiles)  # no new downloads for cached tiles


def test_failed_tiles_are_retried_later(qtbot):
    widget = TileMap(FakeFetch(fail=True))
    qtbot.addWidget(widget)
    widget.resize(300, 300)
    widget.show()
    qtbot.waitUntil(lambda: bool(widget.fetch.urls) and not widget.requested)

    assert widget.tiles == {}
    count = len(widget.fetch.urls)
    widget.repaint()
    qtbot.waitUntil(lambda: len(widget.fetch.urls) > count)


def test_tiles_wrap_around_the_world_and_skip_outside_rows(tile_map):
    tile_map.set_view((80.0, 179.0), 3)
    keys = tile_map.visible_tiles()
    assert all(0 <= y < 8 for _, _, y in keys)
    assert any(x >= 8 for _, x, _ in keys)  # beyond the antimeridian, fetched as x % 8


def test_fit_waits_for_layout(qtbot):
    widget = TileMap(FakeFetch())
    qtbot.addWidget(widget)
    widget.fit([BH, BAMBUI])
    assert widget.pending_fit == [BH, BAMBUI]

    widget.resize(800, 600)
    widget.show()
    qtbot.waitExposed(widget)
    assert widget.pending_fit is None
    assert widget.zoom > 4


def test_zoom_keeps_the_anchor_point_still(tile_map):
    tile_map.set_view(BH, 6)
    anchor = QPointF(100, 100)
    before = unproject(tile_map.top_left() + anchor, tile_map.zoom)

    tile_map.zoom_by(1, anchor)

    after = unproject(tile_map.top_left() + anchor, tile_map.zoom)
    assert tile_map.zoom == 7
    assert after == (pytest.approx(before[0], abs=1e-6), pytest.approx(before[1], abs=1e-6))

    tile_map.set_view(BH, 14)
    tile_map.zoom_by(1)
    assert tile_map.zoom == 14


def test_buttons_and_double_click_zoom(tile_map, qtbot):
    tile_map.set_view(BH, 6)
    buttons = {button.text(): button for button in tile_map.findChildren(QPushButton)}

    qtbot.mouseClick(buttons["+"], Qt.MouseButton.LeftButton)
    assert tile_map.zoom == 7
    qtbot.mouseClick(buttons["−"], Qt.MouseButton.LeftButton)  # noqa: RUF001
    assert tile_map.zoom == 6
    qtbot.mouseDClick(tile_map, Qt.MouseButton.LeftButton, pos=QPoint(400, 300))
    assert tile_map.zoom == 7


def mouse_event(kind, pos, button, buttons):
    point = QPointF(pos)
    return QMouseEvent(kind, point, point, button, buttons, Qt.KeyboardModifier.NoModifier)


def test_drag_pans_the_map(tile_map):
    tile_map.set_view(BH, 8)
    left, none = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton

    tile_map.mousePressEvent(mouse_event(QEvent.Type.MouseButtonPress, QPoint(400, 300), left, left))
    tile_map.mouseMoveEvent(mouse_event(QEvent.Type.MouseMove, QPoint(500, 300), none, left))
    tile_map.mouseReleaseEvent(mouse_event(QEvent.Type.MouseButtonRelease, QPoint(500, 300), left, none))

    assert tile_map.center[1] < BH[1]  # dragging right shows what is west
    assert tile_map.center[0] == pytest.approx(BH[0], abs=1e-6)
    assert not tile_map.dragged


def test_marker_hit_test_and_click(tile_map, qtbot):
    tile_map.set_view(BH, 8)
    tile_map.set_markers([Marker(*BH, "#FF0000", "31", "BH")])
    center = tile_map.to_screen(*BH).toPoint()

    assert tile_map.marker_at(QPointF(center)) == 0
    assert tile_map.marker_at(QPointF(center + QPoint(40, 0))) is None
    with qtbot.waitSignal(tile_map.marker_clicked) as signal:
        qtbot.mouseClick(tile_map, Qt.MouseButton.LeftButton, pos=center)
    assert signal.args == [0]

    qtbot.mouseMove(tile_map, center)
    assert tile_map.hovered == 0
    qtbot.mouseMove(tile_map, center + QPoint(100, 100))
    assert tile_map.hovered is None


# Map page ------------------------------------------------------------------


@pytest.fixture
def map_page(qtbot):
    page = MapPage(FakeFetch())
    qtbot.addWidget(page)
    page.resize(1000, 700)
    page.show()
    qtbot.waitExposed(page)
    return page


def sample(code, name, temp_max, rain, position=None):
    record = make_record(date(2025, 8, 28), code, name).model_copy(update={"temp_max": temp_max, "precipitation": rain})
    if position is None:
        return record.model_copy(update={"latitude": None, "longitude": None})
    return record.model_copy(update={"latitude": position[0], "longitude": position[1]})


def test_markers_use_record_or_catalog_coordinates(map_page):
    records = [sample("A565", "BAMBUI", 31.0, 2.0, BAMBUI), sample("A521", "BH", 28.0, 9.0)]

    map_page.set_records(records, {"A521": BH})

    markers = map_page.map.markers
    assert [m.label for m in markers] == ["28", "31"]  # lowest first: the highest is drawn on top
    assert (markers[0].lat, markers[0].lon) == BH
    assert markers[1].color != markers[0].color
    assert map_page.map.legend.low == "28.0"
    assert map_page.map.legend.high == "31.0"
    assert "média do período" in map_page.map.legend.title
    assert map_page.info_label.text().startswith("2 estação(ões)")
    assert map_page.map.zoom > 4  # framed the two stations


def test_metric_change_and_marker_details(map_page):
    map_page.set_records([sample("A565", "BAMBUI", 31.0, 2.0, BAMBUI), sample("A521", "BH", 28.0, 9.0, BH)])
    map_page.metric_combo.setCurrentText("Precipitação acumulada")

    assert [m.label for m in map_page.map.markers] == ["2", "9"]
    assert "total do período" in map_page.map.legend.title
    map_page.describe(1)
    assert map_page.info_label.text() == "BH (A521): 9.0 mm · Precipitação acumulada"
    assert "<b>BH</b>" in map_page.map.markers[1].tooltip


def test_no_coordinates(map_page):
    map_page.set_records([sample("X1", "NENHUMA", 30.0, 1.0)])
    assert map_page.map.markers == []
    assert map_page.info_label.text() == "Nenhuma estação com coordenadas para exibir."

    map_page.set_records([])
    assert map_page.info_label.text() == ""
    assert map_page.subtitle.text() == "Nenhum dado carregado"
