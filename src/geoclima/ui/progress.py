"""Progress and time-left estimate of a collection, kept apart from widgets so it is trivial to test."""

import time
from collections.abc import Callable


def format_eta(seconds: float) -> str:
    seconds = max(round(seconds), 0)
    if seconds < 60:
        return f"~{seconds} s restantes"
    minutes, seconds = divmod(seconds, 60)
    return f"~{minutes} min {seconds:02d} s restantes"


class ProgressTracker:
    """Counts finished stations and estimates the time left from the average time per station so far."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self.maximum = 0
        self.current = 0
        self.started_at = 0.0

    def start(self, maximum: int) -> None:
        self.maximum = max(maximum, 1)
        self.current = 0
        self.started_at = self.clock()

    def step(self, amount: int = 1) -> None:
        self.current = min(self.current + amount, self.maximum)

    def reset(self) -> None:
        self.maximum = self.current = 0

    @property
    def status(self) -> str:
        if not self.maximum:
            return ""
        text = f"{self.current}/{self.maximum} estações"
        if self.current >= self.maximum:
            return text
        if self.current:
            per_step = (self.clock() - self.started_at) / self.current
            text += f" · {format_eta(per_step * (self.maximum - self.current))}"
        return text
