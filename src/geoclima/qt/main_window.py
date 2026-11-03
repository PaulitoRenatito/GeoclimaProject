from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from geoclima import __version__
from geoclima.qt.charts_page import ChartsPage
from geoclima.qt.theme import checkable, named

PAGES = ["Coleta de Dados", "Histórico", "Gráficos", "Mapa"]
PROTOTYPE_PAGE = "Gráficos"


class MainWindow(QMainWindow):
    """Sidebar navigation instead of tabs. Only the charts page exists in this prototype."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Geoclima - Coletor de Dados Meteorológicos (protótipo Qt)")
        self.resize(1280, 800)
        self.setMinimumSize(1050, 680)

        sidebar = named(QFrame(), "sidebar")
        sidebar.setFixedWidth(200)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(10, 0, 10, 0)
        side.setSpacing(4)
        side.addWidget(named(QLabel("Geoclima"), "appTitle"))
        self.nav = QButtonGroup(self)
        for name in PAGES:
            button = checkable(QPushButton(name))
            button.setEnabled(name == PROTOTYPE_PAGE)
            button.setChecked(name == PROTOTYPE_PAGE)
            if name != PROTOTYPE_PAGE:
                button.setToolTip("Fora do protótipo")
            self.nav.addButton(button)
            side.addWidget(button)
        side.addStretch(1)
        side.addWidget(named(QLabel(f"v{__version__} · protótipo PySide6"), "version"))

        self.charts = ChartsPage()

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar)
        layout.addWidget(self.charts, 1)
        self.setCentralWidget(central)
