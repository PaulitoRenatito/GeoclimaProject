from data.application import weather_data_service
from data.domain.weather_data import WeatherData
from data.domain.weather_data_request import WeatherDataRequest
from data.infrastructure.weather_data_logger import weather_data_logger
from env.secrets import token
from exporter import csv_exporter
from utils.constants import mg_stations_dict
from utils.utils import get_file_name

date: str = '2025-06-25'

requests = [
    WeatherDataRequest(
        date=date,
        station_code=code,
    )
    for name, code in mg_stations_dict.items()
]

response = weather_data_service.get_weather_data_intermittently(
    requests,
    token,
    1,
    on_event=weather_data_logger
)

csv_exporter.export(
    get_file_name(date),
    response,
    WeatherData.model_fields.keys()
)
