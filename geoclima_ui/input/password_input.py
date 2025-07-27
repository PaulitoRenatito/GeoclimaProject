from geoclima_ui.input.exceptions import InputValidationError
from geoclima_ui.input.labeled_input import LabeledInput

class PasswordInput(LabeledInput):
    """Um LabeledInput que oculta o texto para senhas."""
    def __init__(self, parent, label_text, **kwargs):
        super().__init__(parent, label_text, entry_options={'show': '*'}, **kwargs)

    def validate(self):
        """Valida se o texto do Entry não está vazio."""
        if not self.get():
            raise InputValidationError("O campo de Token não pode estar vazio")