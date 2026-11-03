"""Form validation rules, free of any widget so they can be unit tested headless."""

from datetime import date


class InputValidationError(Exception):
    """Raised when a form field holds an invalid value. message is shown to the user."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def validate_token(value: str) -> str:
    value = value.strip()
    if not value:
        raise InputValidationError("O campo de Token não pode estar vazio.")
    return value


def validate_past_date(day: date, today: date | None = None) -> date:
    """INMET only publishes complete daily data for past days, so today and future dates are rejected."""
    if day >= (today or date.today()):
        raise InputValidationError("A data deve ser anterior à data atual.")
    return day


def validate_date_range(initial_date: date, final_date: date | None) -> None:
    if final_date is not None and final_date < initial_date:
        raise InputValidationError("A Data Final não pode ser anterior à Data Inicial.")
