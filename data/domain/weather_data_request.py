from pydantic import BaseModel

class WeatherDataRequest(BaseModel):
    """
    Model representing a request for data records from a weather station.
    """
    initial_date: str
    end_date: str
    station_code: str

    @staticmethod
    def builder() -> '_WeatherDataRequestBuilder':
        """
        Returns a builder for constructing a DadosRequest instance.
        """
        return _WeatherDataRequestBuilder()


class _WeatherDataRequestBuilder:
    """
    Builder for creating a WeatherDataRequest instance.
    """
    def __init__(self):
        self._initial_date = ""
        self._end_date = ""
        self._station_code = ""

    def initial_date(self, data_inicial: str):
        self._initial_date = data_inicial
        return self

    def end_date(self, data_final: str):
        self._end_date = data_final
        return self

    def station_code(self, cod_estacao: str):
        self._station_code = cod_estacao
        return self

    def build(self) -> 'WeatherDataRequest':
        return WeatherDataRequest(
            initial_date=self._initial_date,
            end_date=self._end_date,
            station_code=self._station_code
        )