"""Dark theme of the PySide6 prototype: one Qt stylesheet plus the colors the charts use."""

from typing import TypeVar

from PySide6.QtWidgets import QAbstractButton, QWidget

BACKGROUND = "#1E1F22"
SIDEBAR = "#18191C"
SURFACE = "#2B2D31"
SURFACE_ALT = "#303237"
BORDER = "#3A3C42"
TEXT = "#E6E8EB"
MUTED = "#9AA0A6"
DISABLED = "#5F6368"
ACCENT = "#3B8ED0"
AVERAGE = "#E0B050"
RAIN = "#4FB3BF"

STYLESHEET = f"""
QWidget {{ background: {BACKGROUND}; color: {TEXT}; font-family: "Segoe UI"; font-size: 10pt; }}
QLabel {{ background: transparent; }}

#sidebar {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}
#sidebar QPushButton {{
    text-align: left; padding: 10px 14px; border: none; border-radius: 6px;
    color: {MUTED}; background: transparent;
}}
#sidebar QPushButton:hover {{ color: {TEXT}; }}
#sidebar QPushButton:checked {{ background: {SURFACE}; color: {TEXT}; font-weight: 600; }}
#sidebar QPushButton:disabled {{ color: {DISABLED}; }}
#appTitle {{ font-size: 15pt; font-weight: 700; padding: 18px 14px 14px 14px; }}
#version {{ color: {DISABLED}; font-size: 8.5pt; padding: 12px 14px; }}

#pageTitle {{ font-size: 18pt; font-weight: 600; }}
#subtitle {{ color: {MUTED}; }}

#card, #panel {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}
#cardTitle {{ color: {MUTED}; font-size: 9pt; }}
#cardValue {{ font-size: 19pt; font-weight: 600; }}
#cardDetail {{ color: {MUTED}; font-size: 8.5pt; }}
#panelTitle {{ color: {MUTED}; font-size: 9pt; font-weight: 600; }}

QPushButton {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 14px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton#primary {{ background: {ACCENT}; border: 1px solid {ACCENT}; color: white; font-weight: 600; }}
#segment QPushButton {{ border-radius: 0; padding: 6px 16px; }}
#segment QPushButton:checked {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}

QComboBox {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 6px; padding: 5px 10px; min-width: 190px;
}}
QComboBox:hover {{ border-color: {ACCENT}; }}
QComboBox:disabled {{ color: {DISABLED}; }}
QComboBox QAbstractItemView {{
    background: {SURFACE}; border: 1px solid {BORDER}; selection-background-color: {ACCENT}; outline: none;
}}

QTableView {{
    background: {SURFACE}; alternate-background-color: {SURFACE_ALT}; border: none;
    gridline-color: transparent; selection-background-color: {ACCENT}; selection-color: white;
}}
QTableView::item {{ border: none; padding: 0 6px; }}
QTableView::item:selected, QTableView::item:selected:!active {{ background: {ACCENT}; color: white; }}
QHeaderView::up-arrow, QHeaderView::down-arrow {{ subcontrol-position: center right; width: 10px; padding-right: 4px; }}
QHeaderView::section {{
    background: {SURFACE}; color: {MUTED}; border: none; border-bottom: 1px solid {BORDER}; padding: 6px;
}}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QToolTip {{ background: {SURFACE}; color: {TEXT}; border: 1px solid {ACCENT}; padding: 6px; }}
"""


W = TypeVar("W", bound=QWidget)
B = TypeVar("B", bound=QAbstractButton)


def named(widget: W, name: str) -> W:
    """Sets the objectName the stylesheet selects on (#name). Qt's property kwargs are not in the stubs."""
    widget.setObjectName(name)
    return widget


def checkable(button: B) -> B:
    button.setCheckable(True)
    return button
