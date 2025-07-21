from data.application import weather_data_service
from data.domain.weather_data import WeatherData
from data.domain.weather_data_request import WeatherDataRequest
from data.infrastructure.weather_data_logger import weather_data_logger
from env.secrets import token
from exporter.excel_exporter import ExcelExporter
from utils.constants import mg_stations_dict

date: str = '2025-07-18'

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
    .5,
    on_event=weather_data_logger
)

if response:
    exporter = ExcelExporter(
        date=date,
        data=response,
        fieldnames=WeatherData.model_fields.keys(),
    )
    exporter.export()
else:
    print("Nenhuma resposta recebida do serviço, nenhum arquivo foi gerado.")
