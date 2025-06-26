from typing import Dict, Any
from tqdm import tqdm


class WeatherDataProgressLogger:
    def __init__(self):
        self.progress_bar = None
        self.last_city = ""

    def __call__(self, event: str, data: Dict[str, Any]) -> None:
        if event == "process_started":
            total = data['total_requests']
            self.progress_bar = tqdm(
                total=total,
                desc="Processando estações",
                unit="estação",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} - {postfix}"
            )

        elif event == "request_completed":
            self.last_city = data['station_name']
            if self.progress_bar:
                self.progress_bar.set_postfix_str(f"{self.last_city}")
                self.progress_bar.update(1)

        elif event == "process_completed":
            if self.progress_bar:
                self.progress_bar.set_postfix_str("Concluído!")
                self.progress_bar.close()

weather_data_logger = WeatherDataProgressLogger()