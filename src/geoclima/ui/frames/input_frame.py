from datetime import date, timedelta

import customtkinter

from geoclima.ui.validation import parse_date, parse_optional_date, validate_date_range, validate_token
from geoclima.ui.widgets.date_input import DateInput
from geoclima.ui.widgets.password_input import PasswordInput


class InputFrame(customtkinter.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        label = customtkinter.CTkLabel(self, text="1. Token e Período", font=("", 14, "bold"))
        label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.token_input = PasswordInput(self, label_text="Token INMET:")
        self.token_input.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5, padx=5)

        self.remember_token = customtkinter.CTkCheckBox(self, text="Lembrar token (Cofre de Credenciais do Windows)")
        self.remember_token.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))

        self.initial_date_input = DateInput(self, label_text="Data Inicial:")
        self.initial_date_input.set(date.today() - timedelta(days=1))
        self.initial_date_input.grid(row=3, column=0, sticky="ew", pady=5, padx=5)

        self.final_date_input = DateInput(self, label_text="Data Final:", can_be_empty=True)
        self.final_date_input.grid(row=3, column=1, sticky="ew", pady=5, padx=5)

        hint_label = customtkinter.CTkLabel(
            self,
            text="Datas no formato AAAA-MM-DD. Deixe a Data Final em branco para coletar um único dia.",
            font=("", 12, "italic"),
        )
        hint_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))

    def set_token(self, token: str | None) -> None:
        self.token_input.entry.delete(0, "end")
        if token:
            self.token_input.entry.insert(0, token)
            self.remember_token.select()

    def get_values(self) -> tuple[str, date, date | None]:
        """Validates the inputs and returns (token, initial_date, final_date or None)."""
        token = validate_token(self.token_input.get())
        initial_date = parse_date(self.initial_date_input.get())
        final_date = parse_optional_date(self.final_date_input.get())
        validate_date_range(initial_date, final_date)
        return token, initial_date, final_date
