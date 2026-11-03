from geoclima.ui.widgets.exceptions import InputValidationError
from geoclima.ui.widgets.labeled_input import LabeledInput


class PasswordInput(LabeledInput):
    """A LabeledInput that masks its text."""

    def __init__(self, parent, label_text, **kwargs):
        super().__init__(parent, label_text, entry_options={"show": "*"}, **kwargs)

    def validate(self) -> str:
        value = self.get()
        if not value:
            raise InputValidationError("O campo de Token não pode estar vazio.")
        return value
