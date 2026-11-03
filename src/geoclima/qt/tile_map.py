"""
A slippy map drawn with QPainter: OpenStreetMap tiles in Web Mercator, colored markers, drag to pan,
wheel to zoom. Tiles come from map_tiles.TileFetcher (identifying User-Agent + disk cache, as the OSM
tile policy asks) on a small thread pool, and are shown in grayscale so the colored markers stand out.
"""

import logging
import math
from collections import OrderedDict
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QImage,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import QPushButton, QToolTip, QVBoxLayout, QWidget

from geoclima.qt import theme
from geoclima.qt.theme import named

logger = logging.getLogger(__name__)

TILE_SIZE = 256
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
ATTRIBUTION = "© OpenStreetMap contributors"
MIN_ZOOM, MAX_ZOOM = 3, 14
MAX_FIT_ZOOM = 10
MAX_PARALLEL_DOWNLOADS = 2  # OSM asks apps to keep it low
MEMORY_CACHE_TILES = 400
MARKER_RADIUS = 14
DRAG_THRESHOLD = 4
BRAZIL_CENTER = (-15.8, -47.9)
TILE_SHADE = QColor(24, 25, 28, 150)  # darkens the grayscale tiles towards the app background

TileKey = tuple[int, int, int]  # zoom, x, y
Fetch = Callable[[str], bytes]


def project(lat: float, lon: float, zoom: int) -> QPointF:
    """Latitude/longitude to Web Mercator pixel coordinates at the given zoom."""
    scale = TILE_SIZE * 2**zoom
    lat = max(min(lat, 85.0511), -85.0511)
    sin = math.sin(math.radians(lat))
    x = (lon + 180) / 360 * scale
    y = (0.5 - math.log((1 + sin) / (1 - sin)) / (4 * math.pi)) * scale
    return QPointF(x, y)


def unproject(point: QPointF, zoom: int) -> tuple[float, float]:
    scale = TILE_SIZE * 2**zoom
    lon = point.x() / scale * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * point.y() / scale))))
    return lat, lon


def fit_view(
    points: Sequence[tuple[float, float]], width: int, height: int, margin: int = 60
) -> tuple[tuple[float, float], int]:
    """Center and the largest zoom that shows every point inside the viewport, keeping a margin."""
    if not points:
        return BRAZIL_CENTER, 4
    if len(points) == 1:
        return points[0], MAX_FIT_ZOOM
    for zoom in range(MAX_FIT_ZOOM, MIN_ZOOM - 1, -1):
        projected = [project(lat, lon, zoom) for lat, lon in points]
        xs, ys = [p.x() for p in projected], [p.y() for p in projected]
        if max(xs) - min(xs) <= width - 2 * margin and max(ys) - min(ys) <= height - 2 * margin:
            break
    center = QPointF((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2)
    return unproject(center, zoom), zoom


def text_color_for(background: QColor) -> QColor:
    luminance = 0.299 * background.red() + 0.587 * background.green() + 0.114 * background.blue()
    return QColor("#1E1E1E") if luminance > 150 else QColor("#FFFFFF")


@dataclass(frozen=True)
class Marker:
    lat: float
    lon: float
    color: str
    label: str
    tooltip: str


@dataclass(frozen=True)
class Legend:
    title: str
    colors: list[str]  # from the low to the high end of the scale
    low: str
    high: str


class TileSignals(QObject):
    loaded = Signal(object, bytes)  # key, image bytes
    failed = Signal(object)


class TileDownload(QRunnable):
    def __init__(self, key: TileKey, fetch: Fetch, signals: TileSignals) -> None:
        super().__init__()
        self.key, self.fetch, self.signals = key, fetch, signals

    def run(self) -> None:
        zoom, x, y = self.key
        try:
            data = self.fetch(TILE_URL.format(z=zoom, x=x, y=y))
        except Exception:
            logger.debug("Tile %s failed", self.key, exc_info=True)
            self.signals.failed.emit(self.key)
        else:
            self.signals.loaded.emit(self.key, data)


class TileMap(QWidget):
    marker_clicked = Signal(int)

    def __init__(self, fetch: Fetch | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if fetch is None:
            from geoclima.ui.map_tiles import TileFetcher

            fetch = TileFetcher().fetch
        self.fetch = fetch
        self.center: tuple[float, float] = BRAZIL_CENTER
        self.zoom = 4
        self.markers: list[Marker] = []
        self.legend: Legend | None = None
        self.hovered: int | None = None
        self.pending_fit: list[tuple[float, float]] | None = None

        self.tiles: OrderedDict[TileKey, QPixmap] = OrderedDict()
        self.requested: set[TileKey] = set()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(MAX_PARALLEL_DOWNLOADS)
        self.signals = TileSignals(self)
        self.signals.loaded.connect(self.on_tile_loaded)
        self.signals.failed.connect(self.requested.discard)  # retried the next time it is needed

        self.drag_start: QPoint | None = None
        self.drag_center = QPointF()
        self.dragged = False
        self.setMouseTracking(True)
        self.setMinimumSize(300, 240)

        buttons = QVBoxLayout(self)
        buttons.setContentsMargins(12, 12, 12, 12)
        buttons.setSpacing(4)
        for text, step in (("+", 1), ("−", -1)):  # noqa: RUF001  # typographic minus, on purpose
            button = named(QPushButton(text), "mapButton")
            button.setFixedSize(32, 32)
            button.setToolTip("Aproximar" if step > 0 else "Afastar")
            button.clicked.connect(lambda _=False, s=step: self.zoom_by(s))
            buttons.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)
        buttons.addStretch(1)

    # View ------------------------------------------------------------------

    def set_view(self, center: tuple[float, float], zoom: int) -> None:
        self.center = center
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        self.update()

    def fit(self, points: Sequence[tuple[float, float]]) -> None:
        """Frames the points; waits for a real size if the widget has not been laid out yet."""
        if self.width() < 100 or not self.isVisible():
            self.pending_fit = list(points)
            return
        self.pending_fit = None
        self.set_view(*fit_view(points, self.width(), self.height()))

    def zoom_by(self, step: int, anchor: QPointF | None = None) -> None:
        """Zooms keeping the map point under `anchor` (default: the center) still."""
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom + step))
        if new_zoom == self.zoom:
            return
        anchor = anchor if anchor is not None else QPointF(self.width() / 2, self.height() / 2)
        anchored = unproject(self.top_left() + anchor, self.zoom)
        offset = anchor - QPointF(self.width() / 2, self.height() / 2)
        self.zoom = new_zoom
        self.center = unproject(project(*anchored, new_zoom) - offset, new_zoom)
        self.update()

    def top_left(self) -> QPointF:
        return project(*self.center, self.zoom) - QPointF(self.width() / 2, self.height() / 2)

    def to_screen(self, lat: float, lon: float) -> QPointF:
        return project(lat, lon, self.zoom) - self.top_left()

    def marker_at(self, pos: QPointF) -> int | None:
        for index in reversed(range(len(self.markers))):  # topmost first
            marker = self.markers[index]
            delta = self.to_screen(marker.lat, marker.lon) - pos
            if math.hypot(delta.x(), delta.y()) <= MARKER_RADIUS + 2:
                return index
        return None

    def set_markers(self, markers: list[Marker], legend: Legend | None = None) -> None:
        self.markers = markers
        self.legend = legend
        self.hovered = None
        self.update()

    # Tiles -----------------------------------------------------------------

    def visible_tiles(self) -> list[TileKey]:
        top_left = self.top_left()
        count = 2**self.zoom
        first_x, first_y = math.floor(top_left.x() / TILE_SIZE), math.floor(top_left.y() / TILE_SIZE)
        last_x = math.floor((top_left.x() + self.width()) / TILE_SIZE)
        last_y = math.floor((top_left.y() + self.height()) / TILE_SIZE)
        return [
            (self.zoom, x, y)
            for y in range(max(first_y, 0), min(last_y, count - 1) + 1)
            for x in range(first_x, last_x + 1)
        ]

    def tile(self, key: TileKey) -> QPixmap | None:
        zoom, x, y = key
        wrapped = (zoom, x % 2**zoom, y)
        if wrapped in self.tiles:
            self.tiles.move_to_end(wrapped)
            return self.tiles[wrapped]
        if wrapped not in self.requested:
            self.requested.add(wrapped)
            self.pool.start(TileDownload(wrapped, self.fetch, self.signals))
        return None

    def on_tile_loaded(self, key: TileKey, data: bytes) -> None:
        self.requested.discard(key)
        image = QImage.fromData(data)
        if image.isNull():
            return
        self.tiles[key] = QPixmap.fromImage(image.convertToFormat(QImage.Format.Format_Grayscale8))
        while len(self.tiles) > MEMORY_CACHE_TILES:
            self.tiles.popitem(last=False)
        self.update()

    # Painting --------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(theme.INPUT))

        top_left = self.top_left()
        for key in self.visible_tiles():
            pixmap = self.tile(key)
            if pixmap is not None:
                _, x, y = key
                painter.drawPixmap(QPointF(x * TILE_SIZE, y * TILE_SIZE) - top_left, pixmap)
        painter.fillRect(self.rect(), TILE_SHADE)

        for index, marker in enumerate(self.markers):
            self.paint_marker(painter, marker, hovered=index == self.hovered)
        if self.legend is not None:
            self.paint_legend(painter, self.legend)

        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(theme.MUTED))
        painter.drawText(
            self.rect().adjusted(0, 0, -10, -6), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, ATTRIBUTION
        )
        painter.end()

    def paint_marker(self, painter: QPainter, marker: Marker, hovered: bool) -> None:
        center = self.to_screen(marker.lat, marker.lon)
        radius = MARKER_RADIUS + (3 if hovered else 0)
        color = QColor(marker.color)
        painter.setPen(QPen(QColor(0, 0, 0, 90), 4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius + 1, radius + 1)
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.setBrush(color)
        painter.drawEllipse(center, radius, radius)
        painter.setPen(text_color_for(color))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        box = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, marker.label)

    def paint_legend(self, painter: QPainter, legend: Legend) -> None:
        title_font = QFont("Segoe UI", 8, QFont.Weight.DemiBold)
        width = max(220, QFontMetrics(title_font).horizontalAdvance(legend.title) + 24)
        box = QRectF(12, self.height() - 74, width, 62)
        painter.setPen(QPen(QColor(theme.BORDER), 1))
        painter.setBrush(QColor(theme.SURFACE))
        painter.drawRoundedRect(box, 8, 8)
        painter.setPen(QColor(theme.TEXT))
        painter.setFont(title_font)
        painter.drawText(
            box.adjusted(10, 6, -10, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, legend.title
        )

        bar = QRectF(box.left() + 10, box.top() + 26, box.width() - 20, 10)
        gradient = QLinearGradient(bar.topLeft(), bar.topRight())
        for index, color in enumerate(legend.colors):
            gradient.setColorAt(index / max(len(legend.colors) - 1, 1), QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(bar, 3, 3)

        painter.setPen(QColor(theme.MUTED))
        painter.setFont(QFont("Segoe UI", 8))
        labels = QRectF(bar.left(), bar.bottom() + 2, bar.width(), 16)
        painter.drawText(labels, Qt.AlignmentFlag.AlignLeft, legend.low)
        painter.drawText(labels, Qt.AlignmentFlag.AlignRight, legend.high)

    # Mouse -----------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = event.position().toPoint()
            self.drag_center = project(*self.center, self.zoom)
            self.dragged = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position()
        if self.drag_start is not None:
            delta = pos - QPointF(self.drag_start)
            if self.dragged or delta.manhattanLength() > DRAG_THRESHOLD:
                self.dragged = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.center = unproject(self.drag_center - delta, self.zoom)
                self.update()
            return

        hovered = self.marker_at(pos)
        if hovered != self.hovered:
            self.hovered = hovered
            self.update()
        if hovered is None:
            self.unsetCursor()
            QToolTip.hideText()
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            QToolTip.showText(event.globalPosition().toPoint(), self.markers[hovered].tooltip, self)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if not self.dragged and (index := self.marker_at(event.position())) is not None:
            self.marker_clicked.emit(index)
        self.drag_start = None
        self.dragged = False
        self.unsetCursor()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.zoom_by(1, event.position())

    def wheelEvent(self, event: QWheelEvent) -> None:
        steps = event.angleDelta().y() // 120
        if steps:
            self.zoom_by(1 if steps > 0 else -1, event.position())

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self.pending_fit is not None:
            self.fit(self.pending_fit)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.pending_fit is not None:
            self.fit(self.pending_fit)

    def shutdown(self) -> None:
        """Drops queued downloads and waits briefly for the running ones (called when the window closes)."""
        self.pool.clear()
        self.pool.waitForDone(2000)
