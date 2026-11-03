from collections.abc import Callable
from typing import Any

import customtkinter

from geoclima.ui.colors import value_colors
from geoclima.weather.application.analysis import METRICS, METRICS_BY_LABEL, Metric, StationValue, station_summary
from geoclima.weather.domain.models import WeatherData

# Standard OpenStreetMap tiles: free and keyless, but attribution is required.
# (CARTO's dark tiles would match the theme better, but now require an API key.)
ATTRIBUTION = "© OpenStreetMap contributors"
BRAZIL_CENTER = (-15.8, -47.9)

Coordinates = dict[str, tuple[float, float]]


def create_map_widget(parent) -> Any:
    from tkintermapview import TkinterMapView  # imported lazily: it is slow to load

    from geoclima.ui import map_tiles

    map_tiles.install()
    widget = TkinterMapView(parent, corner_radius=8)
    widget.set_position(*BRAZIL_CENTER)
    widget.set_zoom(4)
    return widget


class MapFrame(customtkinter.CTkFrame):
    """Stations on a map, colored by the chosen metric for the period. Click a marker for details."""

    def __init__(self, parent, map_factory: Callable[[Any], Any] = create_map_widget, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.map_factory = map_factory
        self.map_widget: Any = None
        self.records: list[WeatherData] = []
        self.coordinates: Coordinates = {}
        self.positions: list[tuple[float, float]] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = customtkinter.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_columnconfigure(2, weight=1)
        customtkinter.CTkLabel(toolbar, text="Métrica:").grid(row=0, column=0, padx=(0, 5))
        self.metric_menu = customtkinter.CTkOptionMenu(
            toolbar, values=[m.label for m in METRICS], width=200, command=lambda _: self.render()
        )
        self.metric_menu.grid(row=0, column=1)
        self.info_label = customtkinter.CTkLabel(toolbar, text="", anchor="e")
        self.info_label.grid(row=0, column=2, sticky="e")

        # tkintermapview reads its parent's color to draw rounded corners and fails on "transparent".
        self.map_container = customtkinter.CTkFrame(self, fg_color="#2B2B2B")
        self.map_container.grid(row=1, column=0, sticky="nsew", padx=5)
        self.map_container.grid_columnconfigure(0, weight=1)
        self.map_container.grid_rowconfigure(0, weight=1)

        customtkinter.CTkLabel(self, text=ATTRIBUTION, text_color="gray60", font=("", 10)).grid(
            row=2, column=0, sticky="e", padx=10
        )

    @property
    def metric(self) -> Metric:
        return METRICS_BY_LABEL[self.metric_menu.get()]

    def show(self) -> None:
        """Called when the tab becomes visible: the map widget is only created on first use."""
        if self.map_widget is None:
            self.map_widget = self.map_factory(self.map_container)
            self.map_widget.grid(row=0, column=0, sticky="nsew")
            self.render()

    def set_records(self, records: list[WeatherData], coordinates: Coordinates | None = None) -> None:
        """coordinates (code -> lat, lon) fills in stations whose records carry no position."""
        self.records = records
        self.coordinates = coordinates or {}
        self.render()

    def locate(self, item: StationValue) -> tuple[float, float] | None:
        if item.latitude is not None and item.longitude is not None:
            return item.latitude, item.longitude
        return self.coordinates.get(item.code)

    def render(self) -> None:
        if self.map_widget is None:
            return
        self.map_widget.delete_all_marker()

        metric = self.metric
        located = [(item, pos) for item in station_summary(self.records, metric) if (pos := self.locate(item))]
        if not located:
            self.info_label.configure(text="Nenhuma estação com coordenadas para exibir.")
            return

        colors = value_colors([item.value for item, _ in located], metric)
        for (item, (lat, lon)), color in zip(located, colors, strict=True):
            self.map_widget.set_marker(
                lat,
                lon,
                text=f"{item.value:.0f}",
                marker_color_circle=color,
                marker_color_outside=color,
                text_color="#1E1E1E",
                font=("", 11, "bold"),
                command=lambda _, i=item: self.describe(i),
            )

        self.positions = [pos for _, pos in located]
        # Fitting needs the widget's real size, which Tk only knows once the layout has run.
        self.after(150, self.fit_view)
        self.info_label.configure(text=f"{len(located)} estação(ões) · clique em um marcador para ver detalhes")

    def fit_view(self) -> None:
        if self.map_widget is None or not self.positions:
            return
        lats, lons = [lat for lat, _ in self.positions], [lon for _, lon in self.positions]
        if len(self.positions) == 1:
            self.map_widget.set_position(lats[0], lons[0])
            self.map_widget.set_zoom(9)
            return
        margin = 0.3
        self.map_widget.fit_bounding_box(
            (max(lats) + margin, min(lons) - margin), (min(lats) - margin, max(lons) + margin)
        )

    def describe(self, item: StationValue) -> None:
        metric = self.metric
        self.info_label.configure(text=f"{item.name} ({item.code}): {item.value:.1f} {metric.unit} · {metric.label}")
