from pystreamapi import Stream

from data.application import weather_data_service
from data.domain.weather_data import WeatherData
from data.domain.weather_data_request import WeatherDataRequest
from env.secrets import token
from exporter import csv_exporter

from utils.constants import mg_stations_codes
from utils.utils import get_file_name

data_inicial: str = '2025-05-25'
data_final: str = '2025-05-30'

requests = (Stream.of(mg_stations_codes)
            .map(lambda code: WeatherDataRequest.builder()
                 .initial_date(data_inicial)
                 .end_date(data_final)
                 .station_code(code)
                 .build())
            .to_list())

response = weather_data_service.get_weather_data_intermittently(requests, token, 1)

(Stream.of(response)
.for_each(
    lambda data: csv_exporter.export(
        get_file_name(data[0].DC_NOME, data_inicial, data_final),
        data,
        WeatherData.model_fields.keys()
    )
))
