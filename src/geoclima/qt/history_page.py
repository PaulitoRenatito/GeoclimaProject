import os
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from geoclima.qt.theme import named
from geoclima.qt.widgets import page_header, panel
from geoclima.settings import OUTPUT_DIR

EXPORT_EXTENSIONS = {".csv": "CSV", ".xlsx": "Excel"}
COLUMNS = ["Arquivo", "Tipo", "Tamanho", "Modificado em"]
SORT_ROLE = Qt.ItemDataRole.UserRole
PATH_ROLE = Qt.ItemDataRole.UserRole + 1


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def open_path(path: Path) -> None:
    os.startfile(path)  # Windows only, like the app


def reveal_path(path: Path) -> None:
    subprocess.Popen(["explorer", "/select,", str(path)])


def cell(text: str, sort_value: object, align_right: bool = False) -> QStandardItem:
    item = QStandardItem(text)
    item.setData(sort_value, SORT_ROLE)
    item.setEditable(False)
    if align_right:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return item


class HistoryPage(QWidget):
    """Exported files, newest first. Open them, show them in Explorer, or chart them (double click)."""

    visualize_requested = Signal(Path)

    def __init__(self, output_dir: Path = OUTPUT_DIR) -> None:
        super().__init__()
        self.output_dir = Path(output_dir)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)
        self.summary_label = QLabel()
        folder_button = QPushButton("Abrir pasta")
        folder_button.clicked.connect(self.open_folder)
        root.addLayout(page_header("Histórico", self.summary_label, folder_button))

        frame, layout = panel()
        self.model = QStandardItemModel(0, len(COLUMNS), self)
        self.model.setHorizontalHeaderLabels(COLUMNS)
        self.model.setSortRole(SORT_ROLE)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, len(COLUMNS)):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.table.doubleClicked.connect(lambda _: self.visualize_selected())
        self.table.selectionModel().selectionChanged.connect(lambda *_: self.update_actions())
        layout.addWidget(self.table, 1)

        self.empty_label = named(QLabel("Nenhum arquivo exportado ainda. Faça uma coleta para começar."), "subtitle")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

        actions = QHBoxLayout()
        self.visualize_button = named(QPushButton("Visualizar nos gráficos"), "primary")
        self.visualize_button.clicked.connect(self.visualize_selected)
        self.open_button = QPushButton("Abrir")
        self.open_button.clicked.connect(lambda: self.act_on_selected(open_path))
        self.reveal_button = QPushButton("Mostrar na pasta")
        self.reveal_button.clicked.connect(lambda: self.act_on_selected(reveal_path))
        for button in (self.visualize_button, self.open_button, self.reveal_button):
            actions.addWidget(button)
        actions.addStretch(1)
        actions.addWidget(named(QLabel("Duplo clique abre o arquivo nos gráficos"), "hint"))
        layout.addLayout(actions)
        root.addWidget(frame, 1)

        # Refreshes when an export lands in the folder, even one made outside the app.
        self.watcher = QFileSystemWatcher(self)
        self.watcher.directoryChanged.connect(lambda _: self.refresh())
        self.refresh()

    def list_files(self) -> list[Path]:
        if not self.output_dir.is_dir():
            return []
        files = [p for p in self.output_dir.iterdir() if p.is_file() and p.suffix in EXPORT_EXTENSIONS]
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

    def refresh(self) -> None:
        if self.output_dir.is_dir() and str(self.output_dir) not in self.watcher.directories():
            self.watcher.addPath(str(self.output_dir))

        selected = self.selected_path()
        self.model.removeRows(0, self.model.rowCount())
        for path in self.list_files():
            stat = path.stat()
            name = cell(path.name, path.name.lower())
            name.setData(path, PATH_ROLE)
            name.setToolTip(str(path))
            modified = datetime.fromtimestamp(stat.st_mtime)
            self.model.appendRow(
                [
                    name,
                    cell(EXPORT_EXTENSIONS[path.suffix], path.suffix),
                    cell(format_size(stat.st_size), stat.st_size, align_right=True),
                    cell(modified.strftime("%d/%m/%Y %H:%M"), stat.st_mtime),
                ]
            )
        self.table.sortByColumn(3, Qt.SortOrder.DescendingOrder)

        count = self.model.rowCount()
        self.summary_label.setText(f"{count} arquivo(s) na pasta {self.output_dir.name}")
        self.summary_label.setToolTip(str(self.output_dir))
        self.table.setVisible(count > 0)
        self.empty_label.setVisible(count == 0)
        if selected is not None:
            self.select(selected)
        self.update_actions()

    def select(self, path: Path) -> None:
        for row in range(self.model.rowCount()):
            if self.model.item(row).data(PATH_ROLE) == path:
                self.table.selectRow(row)
                return

    def selected_path(self) -> Path | None:
        rows = self.table.selectionModel().selectedRows()
        return self.model.item(rows[0].row()).data(PATH_ROLE) if rows else None

    def update_actions(self) -> None:
        has_selection = self.selected_path() is not None
        for button in (self.visualize_button, self.open_button, self.reveal_button):
            button.setEnabled(has_selection)

    def act_on_selected(self, action) -> None:
        if (path := self.selected_path()) is not None:
            action(path)

    def visualize_selected(self) -> None:
        self.act_on_selected(self.visualize_requested.emit)

    def open_folder(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        open_path(self.output_dir)
