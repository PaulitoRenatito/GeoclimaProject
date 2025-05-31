from pydantic import BaseModel

class DadosResponse(BaseModel):
    """
    Response model for Dados API.
    """
    nome_estacao: str
    temp_media: float
    temp_minima: float
    temp_maxima: float
    umidade_media: float
    precipitacao_total: float