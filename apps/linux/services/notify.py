"""Notify helper — S17-1: tray + libnotify fallback (X11/Wayland safe)."""

from __future__ import annotations

import shutil
import subprocess


def send(title: str, body: str, urgency: str = "normal") -> bool:
    """Best-effort desktop notification. True if any backend fired."""
    if _via_notify_send(title, body, urgency):
        return True
    return False


def _via_notify_send(title: str, body: str, urgency: str) -> bool:
    if shutil.which("notify-send") is None:
        return False
    try:
        subprocess.run(
            ["notify-send", title, body, f"--urgency={urgency}"],
            check=False,
            timeout=5,
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def tray_message(tray, title: str, body: str) -> bool:
    """Show via QSystemTrayIcon if available. Returns False when headless."""
    try:
        from PySide6.QtWidgets import QSystemTrayIcon

        if tray is None or not QSystemTrayIcon.isSystemTrayAvailable():
            return False
        tray.showMessage(title, body, QSystemTrayIcon.Information, 5000)
        return True
    except (ImportError, RuntimeError, AttributeError):
        return False
