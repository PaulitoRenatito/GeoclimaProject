from pydantic import BaseModel

class DadosRequest(BaseModel):
    """
    Model representing a request for data records from a weather station.
    """
    data_inicial: str
    data_final: str
    cod_estacao: str

    @staticmethod
    def builder() -> '_DadosQuestBuilder':
        """
        Returns a builder for constructing a DadosRequest instance.
        """
        return _DadosQuestBuilder()


class _DadosQuestBuilder:
    """
    Builder for creating a DadosRequest instance.
    """
    def __init__(self):
        self._data_inicial = ""
        self._data_final = ""
        self._cod_estacao = ""

    def data_inicial(self, data_inicial: str):
        self._data_inicial = data_inicial
        return self

    def data_final(self, data_final: str):
        self._data_final = data_final
        return self

    def cod_estacao(self, cod_estacao: str):
        self._cod_estacao = cod_estacao
        return self

    def build(self) -> 'DadosRequest':
        return DadosRequest(
            data_inicial=self._data_inicial,
            data_final=self._data_final,
            cod_estacao=self._cod_estacao
        )