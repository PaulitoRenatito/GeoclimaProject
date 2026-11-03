"""Small building blocks shared by the pages."""

from collections.abc import Sequence

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from geoclima.ui.theme import checkable, named


def panel(title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    """A rounded surface with an optional small caps title; returns the frame and its layout."""
    frame = named(QFrame(), "panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)
    if title:
        layout.addWidget(named(QLabel(title.upper()), "panelTitle"))
    return frame, layout


def page_header(title: str, subtitle: QLabel | None = None, action: QWidget | None = None) -> QHBoxLayout:
    header = QHBoxLayout()
    titles = QVBoxLayout()
    titles.setSpacing(2)
    titles.addWidget(named(QLabel(title), "pageTitle"))
    if subtitle is not None:
        titles.addWidget(named(subtitle, "subtitle"))
    header.addLayout(titles, 1)
    if action is not None:
        header.addWidget(action)
    return header


class SegmentedControl(QFrame):
    """Mutually exclusive buttons drawn as one control, like CTkSegmentedButton."""

    changed = Signal(str)

    def __init__(self, options: Sequence[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("segment")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.group = QButtonGroup(self)
        self.buttons: dict[str, QPushButton] = {}
        for option in options:
            button = checkable(QPushButton(option))
            self.group.addButton(button)
            self.buttons[option] = button
            layout.addWidget(button)
        self.buttons[options[0]].setChecked(True)
        self.group.buttonClicked.connect(lambda button: self.changed.emit(button.text()))

    @property
    def value(self) -> str:
        checked = self.group.checkedButton()
        return checked.text() if checked is not None else ""

    def set_value(self, option: str) -> None:
        self.buttons[option].setChecked(True)
