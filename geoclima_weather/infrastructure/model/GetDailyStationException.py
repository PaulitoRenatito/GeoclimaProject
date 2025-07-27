class GetDailyStationException(Exception):
    """Exception raised for errors in the daily station retrieval process."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"GetDailyStationException: {self.message}"