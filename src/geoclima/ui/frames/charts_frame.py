from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog

import customtkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter
from matplotlib.figure import Figure

from geoclima.settings import OUTPUT_DIR
from geoclima.ui.colors import value_colors
from geoclima.weather.application.analysis import (
    METRICS,
    METRICS_BY_LABEL,
    Metric,
    daily_series,
    describe_dataset,
    highlights,
    station_summary,
)
from geoclima.weather.domain.models import WeatherData

BACKGROUND = "#2B2B2B"
TEXT = "#DCE4EE"
GRID = "#444444"
ACCENT = "#3B8ED0"
RAIN = "#4FB3BF"
AVERAGE = "#E0B050"

VIEW_BY_STATION = "Por estação"
VIEW_OVER_TIME = "Ao longo do período"
ALL_STATIONS = "Média das estações"
MAX_BARS = 25


class ChartsFrame(customtkinter.CTkFrame):
    """Highlights of the loaded data plus one chart: ranking of stations, or evolution over the period."""

    def __init__(self, parent, on_load_file: Callable[[Path], None], output_dir: Path = OUTPUT_DIR, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_load_file = on_load_file
        self.output_dir = output_dir
        self.records: list[WeatherData] = []
        self.station_codes: dict[str, str] = {}  # station name -> code, for the station menu

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        toolbar = customtkinter.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        toolbar.grid_columnconfigure(0, weight=1)
        self.dataset_label = customtkinter.CTkLabel(toolbar, text="", font=("", 14, "bold"), anchor="w")
        self.dataset_label.grid(row=0, column=0, sticky="w")
        customtkinter.CTkButton(toolbar, text="Abrir arquivo...", width=120, command=self.choose_file).grid(
            row=0, column=1
        )

        self.cards = customtkinter.CTkFrame(self, fg_color="transparent")
        self.cards.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        controls = customtkinter.CTkFrame(self, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=5)
        customtkinter.CTkLabel(controls, text="Métrica:").grid(row=0, column=0, padx=(0, 5))
        self.metric_menu = customtkinter.CTkOptionMenu(
            controls, values=[m.label for m in METRICS], width=200, command=lambda _: self.redraw()
        )
        self.metric_menu.grid(row=0, column=1, padx=(0, 15))
        self.view_button = customtkinter.CTkSegmentedButton(
            controls, values=[VIEW_BY_STATION, VIEW_OVER_TIME], command=lambda _: self.redraw()
        )
        self.view_button.set(VIEW_BY_STATION)
        self.view_button.grid(row=0, column=2, padx=(0, 15))
        customtkinter.CTkLabel(controls, text="Estação:").grid(row=0, column=3, padx=(0, 5))
        self.station_menu = customtkinter.CTkOptionMenu(
            controls, values=[ALL_STATIONS], width=240, command=lambda _: self.redraw()
        )
        self.station_menu.grid(row=0, column=4)

        self.figure = Figure(figsize=(8, 4.5), dpi=100, facecolor=BACKGROUND)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=3, column=0, sticky="nsew", padx=5, pady=5)

        self.set_records([], "")

    @property
    def metric(self) -> Metric:
        return METRICS_BY_LABEL[self.metric_menu.get()]

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Abrir arquivo exportado",
            initialdir=self.output_dir,
            filetypes=[("Exportações do Geoclima", "*.csv *.xlsx"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.on_load_file(Path(path))

    def set_records(self, records: list[WeatherData], source: str) -> None:
        self.records = records
        description = describe_dataset(records)
        self.dataset_label.configure(text=f"{source}: {description}" if source else description)

        self.station_codes = {r.station_name: r.station_code for r in sorted(records, key=lambda r: r.station_name)}
        self.station_menu.configure(values=[ALL_STATIONS, *self.station_codes])
        self.station_menu.set(ALL_STATIONS)

        self._render_cards()
        self.redraw()

    def _render_cards(self) -> None:
        for widget in self.cards.winfo_children():
            widget.destroy()
        for column, card in enumerate(highlights(self.records)):
            self.cards.grid_columnconfigure(column, weight=1, uniform="cards")
            box = customtkinter.CTkFrame(self.cards, fg_color=("gray85", "gray20"))
            box.grid(row=0, column=column, sticky="ew", padx=4)
            customtkinter.CTkLabel(box, text=card.title, text_color="gray70").pack(anchor="w", padx=10, pady=(6, 0))
            customtkinter.CTkLabel(box, text=card.value, font=("", 20, "bold")).pack(anchor="w", padx=10)
            customtkinter.CTkLabel(box, text=card.detail, text_color="gray70", font=("", 11)).pack(
                anchor="w", padx=10, pady=(0, 6)
            )

    def redraw(self) -> None:
        over_time = self.view_button.get() == VIEW_OVER_TIME
        self.station_menu.configure(state="normal" if over_time else "disabled")

        self.figure.clear()
        ax = self.figure.add_subplot()
        _style(ax)

        if not self.records:
            ax.axis("off")
            ax.text(0.5, 0.5, "Faça uma coleta ou abra um arquivo do Histórico", color=TEXT, ha="center", va="center")
        elif over_time:
            self._draw_over_time(ax)
        else:
            self._draw_by_station(ax)

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _draw_by_station(self, ax) -> None:
        metric = self.metric
        summary = station_summary(self.records, metric)
        shown = list(reversed(summary[:MAX_BARS]))  # barh draws bottom-up: highest on top

        values = [item.value for item in shown]
        ax.barh([item.name for item in shown], values, color=value_colors(values, metric))
        for index, item in enumerate(shown):
            ax.text(item.value, index, f" {item.value:.1f}", va="center", color=TEXT, fontsize=8)
        title = f"{metric.label} por estação ({metric.unit}, {metric.period_note})"
        if len(summary) > MAX_BARS:
            title += f" · {MAX_BARS} maiores de {len(summary)}"
        ax.set_title(title, color=TEXT, loc="left")
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="x", color=GRID, linewidth=0.5)

    def _draw_over_time(self, ax) -> None:
        metric = self.metric
        selected = self.station_menu.get()
        code = self.station_codes.get(selected)
        series = daily_series(self.records, metric, code)
        days, values = [day for day, _ in series], [value for _, value in series]

        if metric.field == "precipitation":
            ax.bar(days, values, color=RAIN, width=0.7)
        else:
            ax.plot(days, values, color=ACCENT, marker="o", linewidth=2, label=selected)
            if code is not None:
                average = daily_series(self.records, metric)
                ax.plot(
                    [d for d, _ in average], [v for _, v in average], color=AVERAGE, linestyle="--", label=ALL_STATIONS
                )
                ax.legend(facecolor=BACKGROUND, edgecolor=GRID, labelcolor=TEXT)

        ax.set_title(f"{metric.label} · {selected} ({metric.unit})", color=TEXT, loc="left")
        ax.xaxis.set_major_formatter(DateFormatter("%d/%m"))
        ax.grid(axis="y", color=GRID, linewidth=0.5)


def _style(ax) -> None:
    ax.set_facecolor(BACKGROUND)
    ax.tick_params(colors=TEXT)
    for spine in ax.spines.values():
        spine.set_color(GRID)
