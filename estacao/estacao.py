from pydantic import BaseModel

class Estacao(BaseModel):
    """
    Model representing a weather station.
    """
    CD_ESTACAO: str
    CD_OSCAR: str
    CD_WSI: str
    DC_NOME: str
    CD_DISTRITO: str
    FL_CAPITAL: str | None
    TP_ESTACAO: str
    VL_LATITUDE: str
    VL_LONGITUDE: str
    VL_ALTITUDE: str
    SG_ESTADO: str
    SG_ENTIDADE: str
    CD_SITUACAO: str
    DT_FIM_OPERACAO: str | None
    DT_INICIO_OPERACAO: str