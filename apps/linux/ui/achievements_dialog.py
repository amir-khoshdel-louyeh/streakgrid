"""Achievements dialog — S16-1: 8 medals with icon + unlock date."""

from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from core.achievements import ACHIEVEMENTS


class AchievementsDialog(QDialog):
    def __init__(self, conn: sqlite3.Connection, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Achievements")
        layout = QVBoxLayout(self)
        unlocked = {
            r["code"]: r["unlocked_at"]
            for r in conn.execute("SELECT code, unlocked_at FROM achievements")
        }
        self.rows: list[QLabel] = []
        for code, name in ACHIEVEMENTS.items():
            at = unlocked.get(code)
            icon = "🏅" if at else "🔒"
            lab = QLabel(f"{icon} {name} ({code})" + (f" — {at}" if at else ""))
            layout.addWidget(lab)
            self.rows.append(lab)
