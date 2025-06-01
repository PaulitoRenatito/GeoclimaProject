from pydantic import BaseModel

class Dados(BaseModel):
    """
    Model representing a data record from a weather station.
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