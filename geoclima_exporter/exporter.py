from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# Fixed location so the app writes to the same place no matter where it is launched from
# (a relative "output" folder lands next to wherever the user opened the .exe).
OUTPUT_DIR = Path.home() / "Documents" / "Geoclima"


class Exporter(ABC):
    """
    Abstract base class for exporters.
    """

    def __init__(self, date: str, data: list[Any]) -> None:
        """
        Initialize the geoclima_exporter with date, geoclima-weather, and fieldnames.

        :param date: The date for which the geoclima-weather is being exported.
        :param data: The geoclima-weather to be exported.
        :param fieldnames: The field names for the export.
        """
        self.date = date
        self.data = data

    @abstractmethod
    def export(self):
        pass

    @abstractmethod
    def get_file_name(self):
        pass