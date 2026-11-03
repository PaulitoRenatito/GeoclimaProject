from abc import ABC, abstractmethod
from typing import Any

import customtkinter


class LabeledInput(customtkinter.CTkFrame, ABC):
    """Base widget pairing a Label with an Entry. Subclasses define validate()."""

    def __init__(
        self, parent, label_text, default_value=None, can_be_empty=False, entry_width=30, entry_options=None, **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.can_be_empty = can_be_empty
        self.columnconfigure(1, weight=1)

        label = customtkinter.CTkLabel(self, text=label_text)
        label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.entry = customtkinter.CTkEntry(self, width=entry_width, **(entry_options or {}))
        self.entry.grid(row=0, column=1, sticky="ew")

        if default_value is not None:
            self.entry.insert(0, default_value)

    def get(self) -> str:
        """Returns the Entry value without surrounding whitespace."""
        return self.entry.get().strip()

    @abstractmethod
    def validate(self) -> Any:
        """Returns the parsed value, or raises InputValidationError."""
