from geoclima_ui.input.exceptions import InputValidationError
from geoclima_ui.input.labeled_input import LabeledInput


class TextInput(LabeledInput):
    """Um LabeledInput para entrada de texto padrão."""
    def __init__(self, parent, label_text, **kwargs):
        super().__init__(parent, label_text, **kwargs)

    def validate(self):
        """Valida se o texto do Entry não está vazio."""
        if not self.get():
            raise InputValidationError("O campo de texto não pode estar vazio")