from datetime import date

import pytest

from geoclima.ui.validation import InputValidationError, validate_date_range, validate_past_date, validate_token

TODAY = date(2026, 11, 3)


def test_accepts_past_dates():
    assert validate_past_date(date(2025, 8, 28), today=TODAY) == date(2025, 8, 28)


@pytest.mark.parametrize("day", [TODAY, date(2026, 11, 4), date(2030, 1, 1)])
def test_rejects_today_and_future(day):
    with pytest.raises(InputValidationError, match="anterior à data atual"):
        validate_past_date(day, today=TODAY)


def test_date_range():
    validate_date_range(date(2025, 8, 28), None)
    validate_date_range(date(2025, 8, 28), date(2025, 8, 28))
    with pytest.raises(InputValidationError):
        validate_date_range(date(2025, 8, 30), date(2025, 8, 28))


def test_token():
    assert validate_token("  abc ") == "abc"
    with pytest.raises(InputValidationError):
        validate_token("   ")
