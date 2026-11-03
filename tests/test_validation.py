from datetime import date

import pytest

from geoclima.ui.validation import parse_date, parse_optional_date, validate_date_range, validate_token
from geoclima.ui.widgets.exceptions import InputValidationError

TODAY = date(2026, 11, 3)


def test_parses_past_date():
    assert parse_date(" 2025-08-28 ", today=TODAY) == date(2025, 8, 28)


@pytest.mark.parametrize("value", ["", "abc", "2025-13-01", "2025-02-30", "28/08/2025", "2025-8"])
def test_rejects_invalid_dates(value):
    with pytest.raises(InputValidationError):
        parse_date(value, today=TODAY)


@pytest.mark.parametrize("value", ["2026-11-03", "2026-11-04", "2030-01-01"])
def test_rejects_today_and_future(value):
    with pytest.raises(InputValidationError, match="anterior à data atual"):
        parse_date(value, today=TODAY)


def test_optional_date_accepts_empty():
    assert parse_optional_date("  ", today=TODAY) is None


def test_optional_date_still_validates_when_filled():
    with pytest.raises(InputValidationError):
        parse_optional_date("abc", today=TODAY)


def test_date_range():
    validate_date_range(date(2025, 8, 28), None)
    validate_date_range(date(2025, 8, 28), date(2025, 8, 28))
    with pytest.raises(InputValidationError):
        validate_date_range(date(2025, 8, 30), date(2025, 8, 28))


def test_token():
    assert validate_token("  abc ") == "abc"
    with pytest.raises(InputValidationError):
        validate_token("   ")
