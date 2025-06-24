from data.application import weather_data_service
from data.domain.weather_data import WeatherData
from data.domain.weather_data_request import WeatherDataRequest
from data.infrastructure.weather_data_logger import weather_data_logger
from env.secrets import token
from exporter import csv_exporter
from utils.constants import mg_stations_codes
from utils.utils import get_file_name

data_inicial: str = '2025-05-25'
data_final: str = '2025-05-30'

requests = [
    WeatherDataRequest.builder()
    .initial_date(data_inicial)
    .end_date(data_final)
    .station_code(code)
    .build()
    for code in mg_stations_codes
]

response = weather_data_service.get_weather_data_intermittently(
    requests,
    token,
    1,
    on_event=weather_data_logger
)

for data in response:
    csv_exporter.export(
        get_file_name(data[0].DC_NOME, data_inicial, data_final),
        data,
        WeatherData.model_fields.keys()
    )
