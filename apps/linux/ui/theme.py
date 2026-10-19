"""Dark theme — S20-1: tokyonight-like stylesheet for Linux/Qt."""

from __future__ import annotations

TOKYONIGHT_DARK = """
QMainWindow, QWidget {
    background-color: #1a1b26;
    color: #c0caf5;
    font-size: 13px;
}
QTabWidget::pane { border: 1px solid #414868; }
QTabBar::tab {
    background: #24283b;
    color: #a9b1d6;
    padding: 6px 14px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: #414868; color: #c0caf5; }
QPushButton {
    background-color: #24283b;
    border: 1px solid #414868;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover { background-color: #414868; }
QPushButton:pressed { background-color: #7aa2f7; color: #1a1b26; }
QLineEdit, QComboBox, QSpinBox, QDateEdit, QCalendarWidget {
    background-color: #24283b;
    border: 1px solid #414868;
    border-radius: 6px;
    padding: 4px;
}
QListWidget { background-color: #24283b; border: 1px solid #414868; }
QFrame[frameShape="5"] { background-color: #24283b; border: 1px solid #414868; border-radius: 8px; }
QToolTip { background-color: #24283b; color: #c0caf5; border: 1px solid #414868; }
"""


def apply_dark(app) -> None:
    app.setStyleSheet(TOKYONIGHT_DARK)
