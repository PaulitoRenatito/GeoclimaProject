import logging
import sys

import pyqtgraph as pg
from PySide6.QtWidgets import QApplication

# Absolute imports: PyInstaller runs this file as a top-level script, not as part of the package.
from geoclima.ui.main_window import MainWindow
from geoclima.ui.theme import STYLESHEET


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(sys.argv)
    app.setApplicationName("Geoclima")
    app.setStyleSheet(STYLESHEET)
    pg.setConfigOptions(antialias=True)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
