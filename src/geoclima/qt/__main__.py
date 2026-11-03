"""PySide6 prototype of the charts page. Usage: python -m geoclima.qt [exported.csv|.xlsx]"""

import sys
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtWidgets import QApplication

from geoclima.qt.main_window import MainWindow
from geoclima.qt.theme import STYLESHEET


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(sys.argv[:1])
    app.setStyleSheet(STYLESHEET)
    pg.setConfigOptions(antialias=True)

    window = MainWindow()
    if args:
        window.visualize_file(Path(args[0]))
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
