class InputValidationError(Exception):
    """Raised when a form field holds an invalid value. message is shown to the user."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
