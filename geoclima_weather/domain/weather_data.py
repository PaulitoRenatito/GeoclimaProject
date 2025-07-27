from pydantic import BaseModel

class WeatherData(BaseModel):
    """
    Model representing a geoclima-weather record from a weather station.
    """
    DC_NOME: str
    CD_ESTACAO: str
    UF: str
    DT_MEDICAO: str
    TEMP_MED: str | None
    TEMP_MIN: str | None
    TEMP_MAX: str | None
    UMID_MED: str | None
    UMID_MIN: str | None
    VEL_VENTO_MED: str | None
    CHUVA: str | None