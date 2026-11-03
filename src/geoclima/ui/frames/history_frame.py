import os
from pathlib import Path
from tkinter import messagebox

import customtkinter

from geoclima.settings import OUTPUT_DIR

EXPORT_EXTENSIONS = (".csv", ".xlsx")


class HistoryFrame(customtkinter.CTkFrame):
    """Lists the exported files, newest first, and opens them with the default program."""

    def __init__(self, parent, output_dir: Path = OUTPUT_DIR, **kwargs):
        super().__init__(parent, **kwargs)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title_label = customtkinter.CTkLabel(self, text="Histórico de Downloads")
        title_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.scrollable_frame = customtkinter.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.populate_history()

    def populate_history(self):
        """Rebuilds the list from the files currently in the output directory."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        files = sorted(
            (path for path in self.output_dir.iterdir() if path.suffix in EXPORT_EXTENSIONS),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        if not files:
            customtkinter.CTkLabel(self.scrollable_frame, text="Nenhum arquivo encontrado.").pack(pady=10)
            return

        for path in files:
            customtkinter.CTkButton(
                self.scrollable_frame,
                text=path.name,
                anchor="w",
                fg_color="transparent",
                command=lambda p=path: self.open_file(p),
            ).pack(fill="x", padx=5, pady=2)

    def open_file(self, path: Path):
        try:
            os.startfile(path)
        except OSError as e:
            messagebox.showerror("Erro ao Abrir", f"Não foi possível abrir o arquivo '{path}'.\n\nErro: {e}")
