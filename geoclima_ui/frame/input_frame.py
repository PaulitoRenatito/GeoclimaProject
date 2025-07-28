from datetime import datetime, timedelta
import customtkinter

from geoclima_ui.input.date_input import DateInput
from geoclima_ui.input.password_input import PasswordInput


class InputFrame(customtkinter.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        label = customtkinter.CTkLabel(self, text="1. Insira os Dados", font=("", 14, "bold"))
        label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.token_input = PasswordInput(self, label_text="Token INMET:")
        self.token_input.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5, padx=5)

        yesterday_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.initial_date_input = DateInput(self, label_text="Data Inicial (AAAA-MM-DD):", default_value=yesterday_date)
        self.initial_date_input.grid(row=2, column=0, sticky="ew", pady=5, padx=5)

        self.final_date_input = DateInput(self, label_text="Data Final (AAAA-MM-DD):", can_be_empty=True)
        self.final_date_input.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

    def get_values(self):
        """Valida e retorna os valores dos inputs."""
        self.token_input.validate()
        self.initial_date_input.validate()
        self.final_date_input.validate()
        return self.token_input.get(), self.initial_date_input.get(), self.final_date_input.get() or None