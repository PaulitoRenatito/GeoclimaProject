import time
from collections.abc import Callable

import customtkinter


def format_eta(seconds: float) -> str:
    seconds = max(round(seconds), 0)
    if seconds < 60:
        return f"~{seconds} s restantes"
    minutes, seconds = divmod(seconds, 60)
    return f"~{minutes} min {seconds:02d} s restantes"


class ProgressFrame(customtkinter.CTkFrame):
    """Progress bar plus "12/68 estações · ~45 s restantes", estimated from the average time per step."""

    def __init__(self, parent, clock: Callable[[], float] = time.monotonic, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.clock = clock
        self.grid_columnconfigure(0, weight=1)

        self.progress_bar = customtkinter.CTkProgressBar(self, height=10, corner_radius=4)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        self.status_label = customtkinter.CTkLabel(self, text="", anchor="e")
        self.status_label.grid(row=1, column=0, sticky="ew", padx=5)

        self.maximum = 1
        self.current = 0
        self.started_at = 0.0
        self.reset()

    # Not named `configure`: that would shadow the tkinter/CTk method CustomTkinter calls internally.
    def set_maximum(self, maximum: int) -> None:
        self.reset()
        self.maximum = max(maximum, 1)
        self.started_at = self.clock()
        self.status_label.configure(text=f"0/{self.maximum} estações")

    def step(self, amount: int) -> None:
        self.current = min(self.current + amount, self.maximum)
        self.progress_bar.set(self.current / self.maximum)

        text = f"{self.current}/{self.maximum} estações"
        remaining = self.maximum - self.current
        if remaining:
            per_step = (self.clock() - self.started_at) / self.current
            text += f" · {format_eta(per_step * remaining)}"
        self.status_label.configure(text=text)

    def reset(self) -> None:
        self.current = 0
        self.progress_bar.set(0)
        self.status_label.configure(text="")
