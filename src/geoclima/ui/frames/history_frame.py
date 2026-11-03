import os
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

import customtkinter

from geoclima.settings import OUTPUT_DIR

EXPORT_EXTENSIONS = {".csv": "CSV", ".xlsx": "Excel"}


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def describe_file(path: Path) -> str:
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
    return f"{EXPORT_EXTENSIONS[path.suffix]} · {format_size(stat.st_size)} · {modified}"


class HistoryFrame(customtkinter.CTkFrame):
    """Exported files, newest first, with shortcuts to open them, show them in Explorer or chart them."""

    def __init__(
        self,
        parent,
        output_dir: Path = OUTPUT_DIR,
        on_visualize: Callable[[Path], None] | None = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.on_visualize = on_visualize

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = customtkinter.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(toolbar, text="Histórico de Downloads", font=("", 14, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.summary_label = customtkinter.CTkLabel(toolbar, text="", text_color="gray70")
        self.summary_label.grid(row=0, column=1, sticky="w", padx=10)
        customtkinter.CTkButton(toolbar, text="Atualizar", width=100, command=self.populate_history).grid(
            row=0, column=2, padx=5
        )
        customtkinter.CTkButton(toolbar, text="Abrir pasta", width=100, command=self.open_folder).grid(row=0, column=3)

        self.scrollable_frame = customtkinter.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.populate_history()

    def list_files(self) -> list[Path]:
        return sorted(
            (path for path in self.output_dir.iterdir() if path.suffix in EXPORT_EXTENSIONS),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    def populate_history(self):
        """Rebuilds the list from the files currently in the output directory."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        files = self.list_files()
        self.summary_label.configure(text=f"{len(files)} arquivo(s)")

        if not files:
            placeholder = customtkinter.CTkLabel(self.scrollable_frame, text="Nenhum arquivo encontrado.")
            placeholder.grid(row=0, column=0, pady=10)
            return

        for index, path in enumerate(files):
            self._add_row(index, path)

    def _add_row(self, index: int, path: Path) -> None:
        row = customtkinter.CTkFrame(self.scrollable_frame, fg_color=("gray85", "gray20"))
        row.grid(row=index, column=0, sticky="ew", padx=5, pady=3)
        row.grid_columnconfigure(0, weight=1)
        row.path = path  # lets tests find the row of a file

        customtkinter.CTkLabel(row, text=path.name, font=("", 13, "bold"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=10, pady=(6, 0)
        )
        customtkinter.CTkLabel(row, text=describe_file(path), text_color="gray70", anchor="w").grid(
            row=1, column=0, sticky="w", padx=10, pady=(0, 6)
        )

        actions: list[tuple[str, Callable[[Path], object]]] = [
            ("Abrir", self.open_file),
            ("Mostrar na pasta", self.reveal_file),
        ]
        if self.on_visualize:
            actions.append(("Visualizar", self.on_visualize))
        for column, (label, action) in enumerate(actions, start=1):
            customtkinter.CTkButton(row, text=label, width=90, command=lambda a=action: a(path)).grid(
                row=0, column=column, rowspan=2, padx=(0, 8)
            )

    def open_file(self, path: Path):
        try:
            os.startfile(path)
        except OSError as e:
            messagebox.showerror("Erro ao Abrir", f"Não foi possível abrir o arquivo '{path}'.\n\nErro: {e}")

    def reveal_file(self, path: Path):
        subprocess.Popen(["explorer", "/select,", str(path)])

    def open_folder(self):
        self.open_file(self.output_dir)
