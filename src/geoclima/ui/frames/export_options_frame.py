import customtkinter

from geoclima.exporter.service import ExportFormat, ExportMode


class ExportOptionsFrame(customtkinter.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(self, text="3. Exportação", font=("", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 5)
        )

        customtkinter.CTkLabel(self, text="Formato:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.format_button = customtkinter.CTkSegmentedButton(self, values=[f.value for f in ExportFormat])
        self.format_button.grid(row=1, column=1, sticky="w", padx=5, pady=3)

        customtkinter.CTkLabel(self, text="Arquivos:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.mode_button = customtkinter.CTkSegmentedButton(self, values=[m.value for m in ExportMode])
        self.mode_button.grid(row=2, column=1, sticky="w", padx=5, pady=3)

        self.set_values(ExportFormat.CSV, ExportMode.PER_DAY)

    def set_values(self, export_format: ExportFormat, mode: ExportMode) -> None:
        self.format_button.set(export_format.value)
        self.mode_button.set(mode.value)

    @property
    def export_format(self) -> ExportFormat:
        return ExportFormat(self.format_button.get())

    @property
    def mode(self) -> ExportMode:
        return ExportMode(self.mode_button.get())
