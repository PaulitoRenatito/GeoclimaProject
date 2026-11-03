import tkinter

import customtkinter

from geoclima.weather.domain.models import Station
from geoclima.weather.infrastructure.station_catalog import CatalogResult, CatalogSource, states_of

DEFAULT_STATE = "MG"

SOURCE_NOTES = {
    CatalogSource.STALE_CACHE: "Sem conexão com o INMET: usando o catálogo salvo anteriormente.",
    CatalogSource.BUILT_IN: "Sem conexão com o INMET: usando a lista embutida de Minas Gerais.",
}


class StationSelectorFrame(customtkinter.CTkFrame):
    """Pick a state (UF), then check the stations to collect. Operational stations start checked."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.stations: list[Station] = []
        self.rows: list[tuple[Station, tkinter.BooleanVar, customtkinter.CTkCheckBox]] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = customtkinter.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_columnconfigure(2, weight=1)
        customtkinter.CTkLabel(header, text="2. Estações", font=("", 14, "bold")).grid(row=0, column=0, sticky="w")
        self.state_menu = customtkinter.CTkOptionMenu(header, values=[DEFAULT_STATE], width=80, command=self.show_state)
        self.state_menu.grid(row=0, column=1, padx=10)
        self.state_menu.configure(state="disabled")

        # No textvariable: CTkEntry hides its placeholder when one is set.
        self.search_entry = customtkinter.CTkEntry(header, placeholder_text="Buscar estação...")
        self.search_entry.grid(row=0, column=2, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda _: self.apply_filter())

        buttons = customtkinter.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=1, column=0, sticky="ew", padx=10)
        buttons.grid_columnconfigure(2, weight=1)
        customtkinter.CTkButton(buttons, text="Marcar todas", width=110, command=lambda: self.set_visible(True)).grid(
            row=0, column=0, padx=(0, 5)
        )
        customtkinter.CTkButton(
            buttons, text="Desmarcar todas", width=110, command=lambda: self.set_visible(False)
        ).grid(row=0, column=1)
        self.count_label = customtkinter.CTkLabel(buttons, text="")
        self.count_label.grid(row=0, column=2, sticky="e")

        self.note_label = customtkinter.CTkLabel(self, text="", text_color="#E0B050", wraplength=360, justify="left")
        self.note_label.grid(row=2, column=0, sticky="w", padx=10)

        self.list_frame = customtkinter.CTkScrollableFrame(self)
        self.list_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.placeholder = customtkinter.CTkLabel(self.list_frame, text="Carregando estações...")
        self.placeholder.pack(pady=10)

    @property
    def current_state(self) -> str:
        return self.state_menu.get()

    def set_catalog(self, result: CatalogResult, preferred_state: str = DEFAULT_STATE) -> None:
        self.stations = result.stations
        states = states_of(self.stations) or [DEFAULT_STATE]
        self.state_menu.configure(values=states, state="normal")
        self.note_label.configure(text=SOURCE_NOTES.get(result.source, ""))
        self.show_state(preferred_state if preferred_state in states else states[0])

    def show_state(self, state: str) -> None:
        self.state_menu.set(state)
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.rows = []

        for station in sorted((s for s in self.stations if s.state == state), key=lambda s: s.name):
            var = tkinter.BooleanVar(value=station.is_operational)
            label = f"{station.name} ({station.code})" + ("" if station.is_operational else " - em pane")
            checkbox = customtkinter.CTkCheckBox(self.list_frame, text=label, variable=var, command=self.update_count)
            self.rows.append((station, var, checkbox))

        self.apply_filter()

    def search(self, text: str) -> None:
        self.search_entry.delete(0, "end")
        if text:
            self.search_entry.insert(0, text)
        self.apply_filter()

    def apply_filter(self) -> None:
        query = self.search_entry.get().strip().lower()
        for station, _, checkbox in self.rows:
            checkbox.pack_forget()
            if query in station.name.lower() or query in station.code.lower():
                checkbox.pack(anchor="w", padx=5, pady=2)
        self.update_count()

    def set_visible(self, checked: bool) -> None:
        """Checks or unchecks the stations matching the current search."""
        for _, var, checkbox in self.rows:
            if checkbox.winfo_manager():
                var.set(checked)
        self.update_count()

    def selected_stations(self) -> list[Station]:
        return [station for station, var, _ in self.rows if var.get()]

    def update_count(self) -> None:
        self.count_label.configure(text=f"{len(self.selected_stations())} de {len(self.rows)} selecionadas")
