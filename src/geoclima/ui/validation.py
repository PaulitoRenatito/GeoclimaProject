"""Form validation rules, free of any Tk dependency so they can be unit tested headless."""

from datetime import date, datetime

from geoclima.ui.widgets.exceptions import InputValidationError

DATE_FORMAT = "%Y-%m-%d"


def parse_date(value: str, today: date | None = None) -> date:
    """
    Parses a YYYY-MM-DD date. INMET only publishes complete daily data for past days,
    so today and future dates are rejected.
    """
    value = value.strip()
    if not value:
        raise InputValidationError("O campo de data não pode estar vazio.")

    try:
        parsed = datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        raise InputValidationError(f"Data inválida: '{value}'. Use o formato AAAA-MM-DD.") from None

    if parsed >= (today or date.today()):
        raise InputValidationError("A data deve ser anterior à data atual.")

    return parsed


def parse_optional_date(value: str, today: date | None = None) -> date | None:
    """Like parse_date, but an empty value means "not informed"."""
    return parse_date(value, today) if value.strip() else None


def validate_date_range(initial_date: date, final_date: date | None) -> None:
    if final_date is not None and final_date < initial_date:
        raise InputValidationError("A Data Final não pode ser anterior à Data Inicial.")


def validate_token(value: str) -> str:
    value = value.strip()
    if not value:
        raise InputValidationError("O campo de Token não pode estar vazio.")
    return value
