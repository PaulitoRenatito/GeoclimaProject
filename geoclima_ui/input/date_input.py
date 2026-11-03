from datetime import date, datetime

from geoclima_ui.input.exceptions import InputValidationError
from geoclima_ui.input.labeled_input import LabeledInput

DATE_FORMAT = '%Y-%m-%d'


class DateInput(LabeledInput):
    """A LabeledInput that validates dates in the YYYY-MM-DD format."""
    def __init__(self, parent, label_text, **kwargs):
        super().__init__(parent, label_text, **kwargs)

    def get(self):
        """Returns the Entry value without surrounding whitespace."""
        return super().get().strip()

    def validate(self) -> date | None:
        """
        Validates the Entry value and returns it as a date.

        Returns None when the field is optional and empty. INMET only publishes
        complete daily data for past days, so today and future dates are rejected.
        """
        value = self.get()

        if not value:
            if self.can_be_empty:
                return None
            raise InputValidationError("O campo de data não pode estar vazio.")

        try:
            parsed = datetime.strptime(value, DATE_FORMAT).date()
        except ValueError:
            raise InputValidationError(f"Data inválida: '{value}'. Use o formato AAAA-MM-DD.")

        if parsed >= date.today():
            raise InputValidationError("A data deve ser anterior à data atual.")

        return parsed
