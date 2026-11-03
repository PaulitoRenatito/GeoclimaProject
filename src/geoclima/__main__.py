import logging

# Absolute import: PyInstaller runs this file as a top-level script, not as part of the package.
from geoclima.ui.app import WeatherApp


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    WeatherApp().mainloop()


if __name__ == "__main__":
    main()
