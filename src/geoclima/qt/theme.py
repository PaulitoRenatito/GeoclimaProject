"""Dark theme: one Qt stylesheet plus the colors the charts and the map paint with."""

from pathlib import Path
from typing import TypeVar

from PySide6.QtWidgets import QAbstractButton, QWidget

BACKGROUND = "#1E1F22"
SIDEBAR = "#18191C"
SURFACE = "#2B2D31"
SURFACE_ALT = "#303237"
INPUT = "#232428"
BORDER = "#3A3C42"
TEXT = "#E6E8EB"
MUTED = "#9AA0A6"
DISABLED = "#5F6368"
ACCENT = "#3B8ED0"
ACCENT_HOVER = "#4A9BDD"
DANGER = "#C94F4F"
DANGER_HOVER = "#D65E5E"
SUCCESS = "#5DBB63"
WARNING = "#E0B050"
AVERAGE = "#E0B050"
RAIN = "#4FB3BF"

# Qt stylesheets take file paths for images; forward slashes work on Windows too.
CHECK_ICON = (Path(__file__).parent / "assets" / "check.svg").as_posix()

STYLESHEET = f"""
QWidget {{ background: {BACKGROUND}; color: {TEXT}; font-family: "Segoe UI"; font-size: 10pt; }}
QLabel, QCheckBox {{ background: transparent; }}

#sidebar {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}
#sidebar QPushButton {{
    text-align: left; padding: 10px 14px; border: none; border-radius: 6px;
    color: {MUTED}; background: transparent;
}}
#sidebar QPushButton:hover {{ color: {TEXT}; }}
#sidebar QPushButton:checked {{ background: {SURFACE}; color: {TEXT}; font-weight: 600; }}
#sidebar QPushButton:disabled {{ color: {DISABLED}; }}
#appTitle {{ font-size: 15pt; font-weight: 700; padding: 18px 14px 2px 14px; }}
#appSubtitle {{ color: {MUTED}; font-size: 8.5pt; padding: 0 14px 14px 14px; }}
#version {{ color: {DISABLED}; font-size: 8.5pt; padding: 12px 14px; }}

#pageTitle {{ font-size: 18pt; font-weight: 600; }}
#subtitle, #hint {{ color: {MUTED}; }}
#hint {{ font-size: 8.5pt; }}
#note {{ color: {WARNING}; font-size: 9pt; }}

#card, #panel {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}
#card QWidget, #panel QWidget {{ background: transparent; }}
#cardTitle {{ color: {MUTED}; font-size: 9pt; }}
#cardValue {{ font-size: 19pt; font-weight: 600; }}
#cardDetail {{ color: {MUTED}; font-size: 8.5pt; }}
#panelTitle {{ color: {MUTED}; font-size: 9pt; font-weight: 600; }}

QPushButton {{ background: {SURFACE_ALT}; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 14px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: {DISABLED}; border-color: {BORDER}; }}
QPushButton#primary {{ background: {ACCENT}; border: 1px solid {ACCENT}; color: white; font-weight: 600; }}
QPushButton#primary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#primary:disabled {{ background: {SURFACE_ALT}; border-color: {BORDER}; color: {DISABLED}; }}
QPushButton#danger {{ background: {DANGER}; border: 1px solid {DANGER}; color: white; font-weight: 600; }}
QPushButton#danger:hover {{ background: {DANGER_HOVER}; }}
#segment QPushButton {{ background: {INPUT}; border-radius: 0; padding: 6px 16px; }}
#segment QPushButton:checked {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}

QLineEdit, QDateEdit, QComboBox {{
    background: {INPUT}; border: 1px solid {BORDER}; border-radius: 6px; padding: 5px 10px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QLineEdit:disabled, QDateEdit:disabled, QComboBox:disabled {{ color: {DISABLED}; }}
QComboBox {{ min-width: 90px; }}
QComboBox:hover, QDateEdit:hover {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{
    background: {SURFACE}; border: 1px solid {BORDER}; selection-background-color: {ACCENT}; outline: none;
}}
QDateEdit::drop-down {{ border: none; width: 22px; }}

QCalendarWidget QWidget {{ alternate-background-color: {SURFACE_ALT}; }}
QCalendarWidget QToolButton {{ background: transparent; color: {TEXT}; padding: 4px 8px; border-radius: 4px; }}
QCalendarWidget QToolButton:hover {{ background: {SURFACE_ALT}; }}
QCalendarWidget #qt_calendar_navigationbar {{ background: {SURFACE}; }}
QCalendarWidget QAbstractItemView {{
    background: {SURFACE}; color: {TEXT}; selection-background-color: {ACCENT}; selection-color: white;
}}
QCalendarWidget QAbstractItemView:disabled {{ color: {DISABLED}; }}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1px solid {BORDER}; border-radius: 4px; background: {INPUT};
}}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: url({CHECK_ICON}); }}

QProgressBar {{ background: {INPUT}; border: none; border-radius: 4px; max-height: 8px; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 4px; }}

QTextEdit {{
    background: {INPUT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px;
    font-family: "Cascadia Mono", "Consolas"; font-size: 9pt;
}}

QListView, QTableView {{
    background: {INPUT}; alternate-background-color: {SURFACE_ALT}; border: 1px solid {BORDER}; border-radius: 8px;
    gridline-color: transparent; selection-background-color: {ACCENT}; selection-color: white; outline: none;
}}
#panel QTableView {{ background: {SURFACE}; border: none; }}
QListView::item {{ padding: 1px 4px; }}
QListView::item:hover {{ background: {SURFACE_ALT}; }}
QListView::indicator {{
    width: 16px; height: 16px; border: 1px solid {BORDER}; border-radius: 4px; background: {INPUT};
}}
QListView::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: url({CHECK_ICON}); }}
QTableView::item {{ border: none; padding: 0 6px; }}
QTableView::item:selected, QTableView::item:selected:!active {{ background: {ACCENT}; color: white; }}
QHeaderView::up-arrow, QHeaderView::down-arrow {{
    subcontrol-position: center right; width: 10px; padding-right: 4px;
}}
QHeaderView::section {{
    background: {SURFACE}; color: {MUTED}; border: none; border-bottom: 1px solid {BORDER}; padding: 6px;
}}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QToolTip {{ background: {SURFACE}; color: {TEXT}; border: 1px solid {ACCENT}; padding: 6px; }}
QStatusBar {{ background: {SIDEBAR}; color: {MUTED}; border-top: 1px solid {BORDER}; }}
QStatusBar QLabel {{ color: {MUTED}; padding: 0 8px; }}
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


def restyle(widget: QWidget, name: str) -> None:
    """Changes the objectName at runtime; Qt only re-applies the stylesheet after unpolish/polish."""
    widget.setObjectName(name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
