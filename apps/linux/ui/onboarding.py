"""Onboarding — P6: first-run welcome with the 66-day story (like the site)."""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

SETTINGS_KEY = "streakgrid/onboarded"


def is_onboarded() -> bool:
    return bool(QSettings("StreakGrid", "StreakGrid").value(SETTINGS_KEY, False))


def mark_onboarded() -> None:
    QSettings("StreakGrid", "StreakGrid").setValue(SETTINGS_KEY, True)


class WelcomeDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to StreakGrid")
        layout = QVBoxLayout(self)
        title = QLabel("You Are What You Do. Forge the Identity.")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addWidget(QLabel(
            "66 days. That's all it takes.\n\n"
            "UCL researchers found a new behavior becomes automatic after "
            "about 66 days on average — not 21, not overnight. Every day you "
            "check the box, the pattern encodes a little deeper until it stops "
            "requiring willpower. The heatmap is there so you can watch it happen."
        ))
        layout.addWidget(QLabel(
            "100% on-device: everything stays on this computer. "
            "No accounts, no cloud, no tracking."
        ))
        go = QPushButton("Start forging")
        go.clicked.connect(self.accept)
        layout.addWidget(go)


def maybe_welcome(parent: QWidget | None = None) -> bool:
    """Show welcome once. Returns True if it was shown."""
    if is_onboarded():
        return False
    WelcomeDialog(parent).exec()
    mark_onboarded()
    return True
