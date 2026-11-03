from datetime import date

from geoclima.ui.validation import parse_date, parse_optional_date
from geoclima.ui.widgets.labeled_input import LabeledInput


class DateInput(LabeledInput):
    """A LabeledInput holding a YYYY-MM-DD date. Rules live in geoclima.ui.validation."""

    def validate(self) -> date | None:
        """Returns the date, or None when the field is optional and empty."""
        if self.can_be_empty:
            return parse_optional_date(self.get())
        return parse_date(self.get())
