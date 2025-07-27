from datetime import datetime

from geoclima_ui.input.exceptions import InputValidationError
from geoclima_ui.input.labeled_input import LabeledInput


class DateInput(LabeledInput):
    """Um LabeledInput que valida o formato de data (AAAA-MM-DD)."""
    def __init__(self, parent, label_text, **kwargs):
        super().__init__(parent, label_text, **kwargs)

    def validate(self):
        """Valida se o texto do Entry está no formato AAAA-MM-DD."""
        value = self.get()

        if not value and not self.can_be_empty:
            raise InputValidationError("O campo de data não pode estar vazio")

        if value == datetime.today().strftime('%Y-%m-%d'):
            raise InputValidationError("A data não pode ser a data atual")

        year_str, month_str, day_str = value.split('-')

        try:
            year = int(year_str)
            if len(year_str) != 4 or year <= 0:
                raise ValueError()
        except ValueError:
            raise InputValidationError("Ano inválido. Deve ser um número com 4 dígitos.")

        try:
            month = int(month_str)
            if not 1 <= month <= 12:
                raise ValueError()
        except ValueError:
            raise InputValidationError("Mês inválido. Deve estar entre 01 e 12.")

        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            raise InputValidationError("O formato da data deve ser AAAA-MM-DD")