from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QListView, QPushButton, QVBoxLayout, QWidget

from geoclima.qt.theme import named
from geoclima.weather.domain.models import Station
from geoclima.weather.infrastructure.station_catalog import CatalogResult, CatalogSource, states_of

DEFAULT_STATE = "MG"
STATION_ROLE = Qt.ItemDataRole.UserRole

SOURCE_NOTES = {
    CatalogSource.STALE_CACHE: "Sem conexão com o INMET: usando o catálogo salvo anteriormente.",
    CatalogSource.BUILT_IN: "Sem conexão com o INMET: usando a lista embutida de Minas Gerais.",
}


def station_label(station: Station) -> str:
    return f"{station.name} ({station.code})" + ("" if station.is_operational else " · em pane")


class StationSelector(QWidget):
    """Pick a state (UF), then check the stations to collect. Operational stations start checked."""

    selection_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.stations: list[Station] = []
        self.bulk_update = False  # skips per-item count updates; never blockSignals the model (the proxy needs them)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.state_combo = QComboBox()
        self.state_combo.setToolTip("Estado (UF)")
        self.state_combo.setEnabled(False)
        self.state_combo.currentTextChanged.connect(self.show_state)
        top.addWidget(self.state_combo)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nome ou código...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.search)
        top.addWidget(self.search_input, 1)
        layout.addLayout(top)

        buttons = QHBoxLayout()
        self.check_all = QPushButton("Marcar todas")
        self.check_all.clicked.connect(lambda: self.set_visible(True))
        self.uncheck_all = QPushButton("Desmarcar todas")
        self.uncheck_all.clicked.connect(lambda: self.set_visible(False))
        buttons.addWidget(self.check_all)
        buttons.addWidget(self.uncheck_all)
        buttons.addStretch(1)
        self.count_label = named(QLabel(), "subtitle")
        buttons.addWidget(self.count_label)
        layout.addLayout(buttons)

        self.note_label = named(QLabel(), "note")
        self.note_label.setWordWrap(True)
        self.note_label.hide()
        layout.addWidget(self.note_label)

        self.model = QStandardItemModel(self)
        self.model.itemChanged.connect(self.update_count)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.list_view = QListView()
        self.list_view.setModel(self.proxy)
        self.list_view.setUniformItemSizes(True)
        layout.addWidget(self.list_view, 1)

        self.placeholder = named(QLabel("Carregando estações..."), "subtitle")
        layout.addWidget(self.placeholder)
        self.update_count()

    @property
    def current_state(self) -> str:
        return self.state_combo.currentText() or DEFAULT_STATE

    def set_catalog(self, result: CatalogResult, preferred_state: str = DEFAULT_STATE) -> None:
        self.stations = result.stations
        states = states_of(self.stations) or [DEFAULT_STATE]
        note = SOURCE_NOTES.get(result.source, "")
        self.note_label.setText(note)
        self.note_label.setVisible(bool(note))
        self.placeholder.hide()

        self.state_combo.blockSignals(True)
        self.state_combo.clear()
        self.state_combo.addItems(states)
        self.state_combo.blockSignals(False)
        self.state_combo.setEnabled(True)
        self.show_state(preferred_state if preferred_state in states else states[0])

    def show_state(self, state: str) -> None:
        if self.state_combo.currentText() != state:
            self.state_combo.setCurrentText(state)  # re-enters through currentTextChanged
            return
        self.bulk_update = True
        self.model.clear()
        for station in sorted((s for s in self.stations if s.state == state), key=lambda s: s.name):
            item = QStandardItem(station_label(station))
            item.setData(station, STATION_ROLE)
            item.setCheckable(True)
            item.setEditable(False)
            item.setCheckState(Qt.CheckState.Checked if station.is_operational else Qt.CheckState.Unchecked)
            self.model.appendRow(item)
        self.bulk_update = False
        self.update_count()

    def search(self, text: str) -> None:
        if self.search_input.text() != text:
            self.search_input.setText(text)  # re-enters through textChanged
            return
        self.proxy.setFilterFixedString(text.strip())

    def set_visible(self, checked: bool) -> None:
        """Checks or unchecks the stations matching the current search."""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.bulk_update = True
        for row in range(self.proxy.rowCount()):
            self.model.itemFromIndex(self.proxy.mapToSource(self.proxy.index(row, 0))).setCheckState(state)
        self.bulk_update = False
        self.update_count()

    def items(self) -> list[QStandardItem]:
        return [self.model.item(row) for row in range(self.model.rowCount())]

    def selected_stations(self) -> list[Station]:
        return [item.data(STATION_ROLE) for item in self.items() if item.checkState() == Qt.CheckState.Checked]

    def update_count(self) -> None:
        if self.bulk_update:
            return
        self.count_label.setText(f"{len(self.selected_stations())} de {self.model.rowCount()} selecionadas")
        self.selection_changed.emit()
