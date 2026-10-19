"""Tray icon — S17-2: show/hide + minimize-to-tray (X11/Wayland safe)."""

from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


def create_tray(
    host: QWidget,
    on_show: Callable[[], None] | None = None,
    on_quit: Callable[[], None] | None = None,
) -> QSystemTrayIcon | None:
    """Create tray icon; None when no system tray (headless/Wayland w/o tray)."""
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None
    tray = QSystemTrayIcon(QIcon(), host)
    tray.setToolTip("StreakGrid")
    menu = QMenu()
    show_action = menu.addAction("Show")
    show_action.triggered.connect(on_show or host.show)
    quit_action = menu.addAction("Quit")
    quit_action.triggered.connect(on_quit or host.close)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: (on_show or host.show)()
        if reason == QSystemTrayIcon.Trigger
        else None
    )
    tray.show()
    return tray


def minimize_to_tray(window: QWidget, tray: QSystemTrayIcon | None, event) -> bool:
    """Hide to tray on close when tray exists. Returns True if handled."""
    if tray is not None and tray.isVisible():
        event.ignore()
        window.hide()
        return True
    return False
