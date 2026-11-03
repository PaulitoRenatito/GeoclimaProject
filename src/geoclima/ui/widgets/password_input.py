from geoclima.ui.validation import validate_token
from geoclima.ui.widgets.labeled_input import LabeledInput


class PasswordInput(LabeledInput):
    """A LabeledInput that masks its text."""

    def __init__(self, parent, label_text, **kwargs):
        super().__init__(parent, label_text, entry_options={"show": "*"}, **kwargs)

    def validate(self) -> str:
        return validate_token(self.get())
