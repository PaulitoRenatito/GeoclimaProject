from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WeatherData(BaseModel):
    """
    Daily summary of one weather station.

    Field names are domain names; aliases map them to the INMET API keys, so the
    rest of the app never depends on the API naming. INMET sends every number as
    a string (or null), which pydantic converts to float.
    """
    model_config = ConfigDict(populate_by_name=True, frozen=True)

    station_name: str = Field(alias="DC_NOME")
    station_code: str = Field(alias="CD_ESTACAO")
    state: str = Field(alias="UF")
    measurement_date: date = Field(alias="DT_MEDICAO")
    latitude: float | None = Field(default=None, alias="VL_LATITUDE")
    longitude: float | None = Field(default=None, alias="VL_LONGITUDE")
    temp_avg: float | None = Field(default=None, alias="TEMP_MED")
    temp_min: float | None = Field(default=None, alias="TEMP_MIN")
    temp_max: float | None = Field(default=None, alias="TEMP_MAX")
    humidity_avg: float | None = Field(default=None, alias="UMID_MED")
    humidity_min: float | None = Field(default=None, alias="UMID_MIN")
    wind_speed_avg: float | None = Field(default=None, alias="VEL_VENTO_MED")
    precipitation: float | None = Field(default=None, alias="CHUVA")

    @field_validator(
        "latitude", "longitude", "temp_avg", "temp_min", "temp_max",
        "humidity_avg", "humidity_min", "wind_speed_avg", "precipitation",
        mode="before",
    )
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class WeatherDataRequest(BaseModel):
    """Request for the daily records of one station over a date range (inclusive)."""
    model_config = ConfigDict(frozen=True)

    initial_date: date
    final_date: date
    station_code: str
