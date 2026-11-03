from datetime import date, timedelta

import customtkinter

from geoclima.ui.validation import DATE_FORMAT, parse_date, parse_optional_date, validate_date_range, validate_token
from geoclima.ui.widgets.date_input import DateInput
from geoclima.ui.widgets.password_input import PasswordInput


class InputFrame(customtkinter.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        label = customtkinter.CTkLabel(self, text="1. Insira os Dados", font=("", 14, "bold"))
        label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.token_input = PasswordInput(self, label_text="Token INMET:")
        self.token_input.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5, padx=5)

        yesterday = (date.today() - timedelta(days=1)).strftime(DATE_FORMAT)
        self.initial_date_input = DateInput(self, label_text="Data Inicial (AAAA-MM-DD):", default_value=yesterday)
        self.initial_date_input.grid(row=2, column=0, sticky="ew", pady=5, padx=5)

        self.final_date_input = DateInput(self, label_text="Data Final (AAAA-MM-DD):", can_be_empty=True)
        self.final_date_input.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        hint_label = customtkinter.CTkLabel(
            self,
            text="Dica: Deixe a Data Final em branco para coletar dados de um único dia.",
            font=("", 12, "italic"),
        )
        hint_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))

    def get_values(self) -> tuple[str, date, date | None]:
        """Validates the inputs and returns (token, initial_date, final_date or None)."""
        token = validate_token(self.token_input.get())
        initial_date = parse_date(self.initial_date_input.get())
        final_date = parse_optional_date(self.final_date_input.get())
        validate_date_range(initial_date, final_date)
        return token, initial_date, final_date
