"""Themes — U4: tokyonight dark + light with persisted toggle."""

from __future__ import annotations

from PySide6.QtCore import QSettings

THEME_KEY = "streakgrid/dark"

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

TOKYONIGHT_LIGHT = """
QMainWindow, QWidget {
    background-color: #f6f8fa;
    color: #1f2328;
    font-size: 13px;
}
QTabWidget::pane { border: 1px solid #d0d7de; }
QTabBar::tab {
    background: #eaeef2;
    color: #57606a;
    padding: 6px 14px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: #ffffff; color: #1f2328; }
QPushButton {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover { background-color: #eaeef2; }
QPushButton:pressed { background-color: #0969da; color: #ffffff; }
QLineEdit, QComboBox, QSpinBox, QDateEdit, QCalendarWidget {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 4px;
}
QListWidget { background-color: #ffffff; border: 1px solid #d0d7de; }
QFrame[frameShape="5"] { background-color: #ffffff; border: 1px solid #d0d7de; border-radius: 8px; }
QToolTip { background-color: #ffffff; color: #1f2328; border: 1px solid #d0d7de; }
"""


def apply_dark(app) -> None:
    app.setStyleSheet(TOKYONIGHT_DARK)


def is_dark() -> bool:
    return bool(QSettings("StreakGrid", "StreakGrid").value(THEME_KEY, True))


def set_dark(dark: bool) -> None:
    QSettings("StreakGrid", "StreakGrid").setValue(THEME_KEY, bool(dark))


def apply_theme(app) -> bool:
    """Apply persisted theme. Returns current dark flag."""
    dark = is_dark()
    app.setStyleSheet(TOKYONIGHT_DARK if dark else TOKYONIGHT_LIGHT)
    return dark
