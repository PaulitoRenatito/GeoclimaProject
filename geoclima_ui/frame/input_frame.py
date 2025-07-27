from datetime import datetime, timedelta
from tkinter import ttk

from geoclima_ui.input.date_input import DateInput
from geoclima_ui.input.password_input import PasswordInput


class InputFrame(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="1. Insira os Dados", padding="10", **kwargs)
        self.columnconfigure(1, weight=1)

        self.token_input = PasswordInput(self, label_text="Token INMET:")
        self.token_input.grid(row=0, column=0, sticky="ew", pady=5)

        yesterday_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.date_input = DateInput(self, label_text="Data (AAAA-MM-DD):", default_value=yesterday_date)
        self.date_input.grid(row=1, column=0, sticky="ew", pady=5)

    def get_values(self):
        """Valida e retorna os valores dos inputs."""
        self.token_input.validate()
        self.date_input.validate()
        return self.token_input.get(), self.date_input.get()