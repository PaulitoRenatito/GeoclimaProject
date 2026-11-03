class StationDataError(Exception):
    """Raised when the daily data of a station cannot be retrieved from INMET."""


class StationCatalogError(Exception):
    """Raised when the INMET station catalog cannot be retrieved or parsed."""
