import datetime

from pydantic import BaseModel, Field, field_validator


class WeatherDataRequest(BaseModel):
    """
    Model representing a request for weather records from a weather station.

    Attributes:
        initial_date (datetime.date):
            The date of the first record in the format YYYY-MM-DD.
        final_date (datetime.date):
            The date of the last record in the format YYYY-MM-DD.
        station_code (str):
            The code of the weather station.
    """
    initial_date: datetime.date = Field(..., description="Date of the first record in the format YYYY-MM-DD")
    final_date: datetime.date = Field(..., description="Date of the last record in the format YYYY-MM-DD")
    station_code: str = Field(..., description="Code of the weather station")

    @field_validator('initial_date', 'final_date', mode='before')
    @classmethod
    def parse_date(cls, v: any) -> datetime.date:
        if isinstance(v, str):
            try:
                return datetime.datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"O formato da data '{v}' é inválido. Use 'AAAA-MM-DD'.")
        return v
