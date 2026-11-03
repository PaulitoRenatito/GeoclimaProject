from datetime import date
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QCursor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableView,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from geoclima.settings import OUTPUT_DIR
from geoclima.ui import theme
from geoclima.ui.colors import value_colors
from geoclima.ui.theme import checkable, named
from geoclima.weather.application.analysis import (
    METRICS,
    METRICS_BY_LABEL,
    Metric,
    StationValue,
    daily_series,
    describe_dataset,
    highlights,
    station_summary,
)
from geoclima.weather.domain.models import WeatherData

VIEW_BY_STATION = "Por estação"
VIEW_OVER_TIME = "Ao longo do período"
ALL_STATIONS = "Média das estações"
MAX_BARS = 25
MAX_DAY_TICKS = 12
SORT_ROLE = Qt.ItemDataRole.UserRole


def card(title: str, value: str, detail: str) -> QFrame:
    frame = named(QFrame(), "card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 10, 14, 10)
    layout.setSpacing(2)
    for text, name in ((title, "cardTitle"), (value, "cardValue"), (detail, "cardDetail")):
        layout.addWidget(named(QLabel(text), name))
    return frame


class ChartsPage(QWidget):
    """Highlights, an interactive chart (station ranking or daily evolution) and a sortable ranking table."""

    file_requested = Signal(Path)  # "Abrir arquivo..." picked an export; the window reads it

    def __init__(self, output_dir: Path = OUTPUT_DIR) -> None:
        super().__init__()
        self.output_dir = output_dir
        self.records: list[WeatherData] = []
        self.station_codes: dict[str, str] = {}
        self.hover_bars: list[StationValue] = []
        self.hover_days: list[date] = []
        self.hover_series: dict[str, dict[date, float]] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(named(QLabel("Gráficos"), "pageTitle"))
        self.subtitle = named(QLabel(), "subtitle")
        titles.addWidget(self.subtitle)
        header.addLayout(titles, 1)
        open_button = named(QPushButton("Abrir arquivo..."), "primary")
        open_button.clicked.connect(self.choose_file)
        header.addWidget(open_button, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        self.cards = QGridLayout()
        self.cards.setSpacing(12)
        root.addLayout(self.cards)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(QLabel("Métrica"))
        self.metric_combo = QComboBox()
        self.metric_combo.addItems([m.label for m in METRICS])
        self.metric_combo.currentTextChanged.connect(self.redraw)
        controls.addWidget(self.metric_combo)
        controls.addSpacing(10)

        segment = named(QFrame(), "segment")
        segment_layout = QHBoxLayout(segment)
        segment_layout.setContentsMargins(0, 0, 0, 0)
        segment_layout.setSpacing(0)
        self.view_group = QButtonGroup(self)
        for text in (VIEW_BY_STATION, VIEW_OVER_TIME):
            button = checkable(QPushButton(text))
            self.view_group.addButton(button)
            segment_layout.addWidget(button)
        self.view_group.buttons()[0].setChecked(True)
        self.view_group.buttonClicked.connect(self.redraw)
        controls.addWidget(segment)
        controls.addSpacing(10)

        controls.addWidget(QLabel("Estação"))
        self.station_combo = QComboBox()
        self.station_combo.setMinimumWidth(260)
        self.station_combo.currentTextChanged.connect(self.redraw)
        controls.addWidget(self.station_combo)
        controls.addStretch(1)
        root.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(12)
        splitter.addWidget(self._build_chart_panel())
        splitter.addWidget(self._build_ranking_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        self.set_records([], "")

    def _build_chart_panel(self) -> QFrame:
        panel = named(QFrame(), "panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)

        self.plot = pg.PlotWidget(background=theme.SURFACE)
        self.plot.setMenuEnabled(False)
        self.plot.showGrid(x=True, y=True, alpha=0.12)
        for name in ("left", "bottom"):
            axis = self.plot.getAxis(name)
            axis.setPen(theme.BORDER)
            axis.setTextPen(theme.MUTED)
        self.legend = self.plot.addLegend(offset=(-10, 10), labelTextColor=theme.TEXT, brush=theme.SURFACE)
        self.crosshair = pg.InfiniteLine(angle=90, pen=pg.mkPen(theme.MUTED, style=Qt.PenStyle.DashLine))
        self.plot.scene().sigMouseMoved.connect(self.on_mouse_moved)
        layout.addWidget(self.plot)

        hint = QLabel("Passe o mouse para ver os valores · role para dar zoom no período · A restaura a vista")
        hint.setObjectName("cardDetail")
        layout.addWidget(hint)
        return panel

    def _build_ranking_panel(self) -> QFrame:
        panel = named(QFrame(), "panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        self.ranking_title = named(QLabel(), "panelTitle")
        layout.addWidget(self.ranking_title)

        self.ranking_model = QStandardItemModel(0, 2, self)
        self.ranking_model.setSortRole(SORT_ROLE)
        self.ranking = QTableView()
        self.ranking.setModel(self.ranking_model)
        self.ranking.setSortingEnabled(True)
        self.ranking.setAlternatingRowColors(True)
        self.ranking.setShowGrid(False)
        self.ranking.verticalHeader().hide()
        self.ranking.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ranking.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ranking.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ranking.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.ranking.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.ranking.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.ranking.doubleClicked.connect(lambda index: self.show_station(self.ranking_model.item(index.row()).text()))
        layout.addWidget(self.ranking, 1)

        hint = QLabel("Clique no cabeçalho para ordenar · duplo clique abre a evolução da estação")
        hint.setObjectName("cardDetail")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return panel

    @property
    def current_metric(self) -> Metric:
        return METRICS_BY_LABEL[self.metric_combo.currentText()]

    @property
    def over_time(self) -> bool:
        checked = self.view_group.checkedButton()
        return checked is not None and checked.text() == VIEW_OVER_TIME

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir arquivo exportado", str(self.output_dir), "Exportações do Geoclima (*.csv *.xlsx)"
        )
        if path:
            self.file_requested.emit(Path(path))

    def set_records(self, records: list[WeatherData], source: str) -> None:
        self.records = records
        description = describe_dataset(records)
        self.subtitle.setText(f"{source} · {description}" if source else description)

        self.station_codes = {r.station_name: r.station_code for r in sorted(records, key=lambda r: r.station_name)}
        self.station_combo.blockSignals(True)
        self.station_combo.clear()
        self.station_combo.addItems([ALL_STATIONS, *self.station_codes])
        self.station_combo.blockSignals(False)

        while self.cards.count():
            item = self.cards.takeAt(0)
            if item is not None and (widget := item.widget()):
                widget.deleteLater()
        for column, highlight in enumerate(highlights(records)):
            self.cards.addWidget(card(highlight.title, highlight.value, highlight.detail), 0, column)

        self.redraw()

    def show_station(self, name: str) -> None:
        self.station_combo.setCurrentText(name)
        self.view_group.buttons()[1].setChecked(True)
        self.redraw()

    def redraw(self) -> None:
        self.station_combo.setEnabled(self.over_time)
        self.plot.clear()
        self.legend.clear()
        self.hover_bars, self.hover_days, self.hover_series = [], [], {}
        self._fill_ranking()

        if not self.records:
            self.plot.setTitle("Faça uma coleta ou abra um arquivo exportado", color=theme.MUTED)
            self.plot.getAxis("left").setTicks(None)
            self.plot.getAxis("bottom").setTicks(None)
        elif self.over_time:
            self._draw_over_time()
        else:
            self._draw_by_station()

    def _fill_ranking(self) -> None:
        metric = self.current_metric
        self.ranking_title.setText(f"RANKING · {metric.label.upper()} ({metric.period_note})")
        self.ranking_model.removeRows(0, self.ranking_model.rowCount())
        self.ranking_model.setHorizontalHeaderLabels(["Estação", metric.unit])
        for item in station_summary(self.records, metric):
            name = QStandardItem(item.name)
            name.setData(item.name, SORT_ROLE)
            value = QStandardItem(f"{item.value:.1f}")
            value.setData(item.value, SORT_ROLE)
            value.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ranking_model.appendRow([name, value])
        self.ranking.sortByColumn(1, Qt.SortOrder.DescendingOrder)

        selected = self.station_combo.currentText() if self.over_time else None
        matches = self.ranking_model.findItems(selected) if selected else []
        if matches:
            self.ranking.selectRow(matches[0].row())
        else:
            self.ranking.clearSelection()

    def _draw_by_station(self) -> None:
        metric = self.current_metric
        summary = station_summary(self.records, metric)
        shown = list(reversed(summary[:MAX_BARS]))  # bars are drawn bottom-up: highest on top
        values = [item.value for item in shown]
        brushes = [pg.mkBrush(color) for color in value_colors(values, metric)]

        self.plot.addItem(
            pg.BarGraphItem(x0=0, y=list(range(len(shown))), height=0.7, width=values, brushes=brushes, pen=None)
        )
        for index, item in enumerate(shown):
            label = pg.TextItem(f" {item.value:.1f}", color=theme.TEXT, anchor=(0, 0.5))
            label.setPos(item.value, index)
            self.plot.addItem(label)

        self.plot.getAxis("left").setTicks([[(i, item.name) for i, item in enumerate(shown)]])
        self.plot.getAxis("bottom").setTicks(None)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setXRange(min(0.0, *values), max(values) * 1.18, padding=0)  # room for the value labels
        self.plot.setYRange(-0.6, len(shown) - 0.4, padding=0)

        title = f"{metric.label} por estação ({metric.unit}, {metric.period_note})"
        if len(summary) > MAX_BARS:
            title += f" · {MAX_BARS} maiores de {len(summary)}"
        self.plot.setTitle(title, color=theme.TEXT, size="11pt")
        self.hover_bars = shown

    def _draw_over_time(self) -> None:
        metric = self.current_metric
        selected = self.station_combo.currentText()
        code = self.station_codes.get(selected)
        days = sorted({r.measurement_date for r in self.records})
        position = {day: i for i, day in enumerate(days)}

        series = dict(daily_series(self.records, metric, code))
        x = [position[day] for day in series]
        if metric.field == "precipitation":
            self.plot.addItem(pg.BarGraphItem(x=x, height=list(series.values()), width=0.7, brush=theme.RAIN, pen=None))
        else:
            self.plot.plot(
                x,
                list(series.values()),
                pen=pg.mkPen(theme.ACCENT, width=2.5),
                symbol="o",
                symbolSize=8,
                symbolBrush=theme.ACCENT,
                symbolPen=None,
                name=selected,
            )
        self.hover_series = {selected: series}

        if code is not None and metric.field != "precipitation":
            average = dict(daily_series(self.records, metric))
            self.plot.plot(
                [position[day] for day in average],
                list(average.values()),
                pen=pg.mkPen(theme.AVERAGE, width=2, style=Qt.PenStyle.DashLine),
                name=ALL_STATIONS,
            )
            self.hover_series[ALL_STATIONS] = average

        step = max(1, len(days) // MAX_DAY_TICKS)
        self.plot.getAxis("bottom").setTicks([[(i, d.strftime("%d/%m")) for i, d in enumerate(days) if i % step == 0]])
        self.plot.getAxis("left").setTicks(None)
        self.plot.setMouseEnabled(x=True, y=False)
        self.plot.enableAutoRange()
        self.plot.setTitle(f"{metric.label} · {selected} ({metric.unit})", color=theme.TEXT, size="11pt")

        self.crosshair.hide()
        self.plot.addItem(self.crosshair, ignoreBounds=True)
        self.hover_days = days

    def tooltip_at(self, point: QPointF) -> str | None:
        """Text shown under the mouse, given a point in chart coordinates."""
        unit = self.current_metric.unit
        if self.hover_bars:
            index = round(point.y())
            if 0 <= index < len(self.hover_bars):
                item = self.hover_bars[index]
                return f"<b>{item.name}</b> ({item.code})<br>{item.value:.1f} {unit}"
        elif self.hover_days:
            index = round(point.x())
            if 0 <= index < len(self.hover_days):
                day = self.hover_days[index]
                lines = [f"<b>{day.strftime('%d/%m/%Y')}</b>"]
                lines += [
                    f"{name}: {values[day]:.1f} {unit}" for name, values in self.hover_series.items() if day in values
                ]
                return "<br>".join(lines)
        return None

    def on_mouse_moved(self, scene_pos: QPointF) -> None:
        view = self.plot.getPlotItem().getViewBox()
        inside = view.sceneBoundingRect().contains(scene_pos)
        text = self.tooltip_at(view.mapSceneToView(scene_pos)) if inside else None
        if text is None:
            QToolTip.hideText()
            self.crosshair.hide()
            return
        if self.hover_days:
            self.crosshair.setPos(round(view.mapSceneToView(scene_pos).x()))
            self.crosshair.show()
        QToolTip.showText(QCursor.pos(), text, self.plot)
