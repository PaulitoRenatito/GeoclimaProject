from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from geoclima.ui.colors import value_colors
from geoclima.ui.theme import named
from geoclima.ui.widgets.common import page_header, panel
from geoclima.ui.widgets.tile_map import Fetch, Legend, Marker, TileMap
from geoclima.weather.application.analysis import (
    METRICS,
    METRICS_BY_LABEL,
    Metric,
    StationValue,
    describe_dataset,
    station_summary,
)
from geoclima.weather.domain.models import WeatherData

Coordinates = dict[str, tuple[float, float]]
LEGEND_STEPS = 9


class MapPage(QWidget):
    """Stations on the map, colored and labeled by the chosen metric for the whole period."""

    def __init__(self, fetch: Fetch | None = None) -> None:
        super().__init__()
        self.records: list[WeatherData] = []
        self.coordinates: Coordinates = {}
        self.shown: list[StationValue] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)
        self.subtitle = QLabel()
        root.addLayout(page_header("Mapa", self.subtitle))

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Métrica"))
        self.metric_combo = QComboBox()
        self.metric_combo.addItems([m.label for m in METRICS])
        self.metric_combo.setMinimumWidth(220)
        self.metric_combo.currentTextChanged.connect(lambda _: self.refresh_markers())
        controls.addWidget(self.metric_combo)
        controls.addStretch(1)
        self.info_label = named(QLabel(), "subtitle")
        controls.addWidget(self.info_label)
        root.addLayout(controls)

        frame, layout = panel()
        layout.setContentsMargins(6, 6, 6, 6)
        self.map = TileMap(fetch)
        self.map.marker_clicked.connect(self.describe)
        layout.addWidget(self.map)
        root.addWidget(frame, 1)
        root.addWidget(named(QLabel("Arraste para mover · role ou dê duplo clique para aproximar"), "hint"))

        self.set_records([])

    @property
    def current_metric(self) -> Metric:
        return METRICS_BY_LABEL[self.metric_combo.currentText()]

    def set_records(self, records: list[WeatherData], coordinates: Coordinates | None = None) -> None:
        """coordinates (code -> lat, lon) fill in stations whose records carry no position."""
        self.records = records
        self.coordinates = coordinates or {}
        self.subtitle.setText(describe_dataset(records))
        self.refresh_markers(fit=True)

    def locate(self, item: StationValue) -> tuple[float, float] | None:
        if item.latitude is not None and item.longitude is not None:
            return item.latitude, item.longitude
        return self.coordinates.get(item.code)

    def refresh_markers(self, fit: bool = False) -> None:
        metric = self.current_metric
        located = [(item, pos) for item in station_summary(self.records, metric) if (pos := self.locate(item))]
        # Drawn lowest first, so the highest values end up on top where markers overlap.
        located.reverse()
        self.shown = [item for item, _ in located]

        if not located:
            self.map.set_markers([])
            self.info_label.setText("Nenhuma estação com coordenadas para exibir." if self.records else "")
            if fit:
                self.map.fit([])
            return

        values = [item.value for item in self.shown]
        colors = value_colors(values, metric)
        markers = [
            Marker(lat, lon, color, f"{item.value:.0f}", self.tooltip(item, metric))
            for (item, (lat, lon)), color in zip(located, colors, strict=True)
        ]
        scale = value_colors(
            [min(values) + (max(values) - min(values)) * i / (LEGEND_STEPS - 1) for i in range(LEGEND_STEPS)], metric
        )
        legend = Legend(
            f"{metric.label} ({metric.unit}, {metric.period_note})",
            scale,
            f"{min(values):.1f}",
            f"{max(values):.1f}",
        )
        self.map.set_markers(markers, legend)
        if fit:
            self.map.fit([pos for _, pos in located])
        self.info_label.setText(f"{len(located)} estação(ões) · clique num marcador para ver os detalhes")

    @staticmethod
    def tooltip(item: StationValue, metric: Metric) -> str:
        return f"<b>{item.name}</b> ({item.code})<br>{item.value:.1f} {metric.unit}"

    def describe(self, index: int) -> None:
        item, metric = self.shown[index], self.current_metric
        self.info_label.setText(f"{item.name} ({item.code}): {item.value:.1f} {metric.unit} · {metric.label}")
