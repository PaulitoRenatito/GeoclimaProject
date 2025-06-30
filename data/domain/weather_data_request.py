from pydantic import BaseModel


class WeatherDataRequest(BaseModel):
    """
    Model representing a request for data records from a weather station.
    """
    date: str
    station_code: str
