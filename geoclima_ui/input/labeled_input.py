from abc import ABC, abstractmethod
from tkinter import ttk


class LabeledInput(ttk.Frame, ABC):
    """Widget base que combina um Label e um Entry."""
    def __init__(
            self,
            parent,
            label_text,
            default_value=None,
            can_be_empty=False,
            entry_width=30,
            entry_options=None,
            **kwargs
    ):
        super().__init__(parent, **kwargs)
        if entry_options is None:
            entry_options = {}

        self.columnconfigure(1, weight=1)

        label = ttk.Label(self, text=label_text)
        label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.entry = ttk.Entry(self, width=entry_width, **entry_options)
        self.entry.grid(row=0, column=1, sticky="ew")

        if default_value is not None:
            self.entry.insert(0, default_value)

    def get(self):
        """Retorna o valor atual do Entry."""
        return self.entry.get()

    def insert(self, index, text):
        """Insere texto no Entry."""
        self.entry.insert(index, text)

    @abstractmethod
    def validate(self):
        """Método de validação base."""
        pass