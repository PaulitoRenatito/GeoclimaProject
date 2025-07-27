class InputValidationError(Exception):
    """Exception raised for errors in the input validation."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"InputValidationError: {self.message}"