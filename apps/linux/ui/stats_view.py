"""Stats view — S15-1: rates + best streak per habit."""

from __future__ import annotations

import sqlite3
from datetime import date

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.streak import best_streak, completion_rate, current_streak
from db.store import get_completions, list_habits, list_pauses


class StatsView(QWidget):
    def __init__(self, conn: sqlite3.Connection, parent=None) -> None:
        super().__init__(parent)
        self.conn = conn
        self.layout = QVBoxLayout(self)
        self.summary = QLabel("")
        self.layout.addWidget(self.summary)
        self.rows: list[QLabel] = []

    def refresh(self, today: str | None = None) -> None:
        today_iso = today or date.today().isoformat()
        for r in self.rows:
            self.layout.removeWidget(r)
            r.deleteLater()
        self.rows = []
        habits = list_habits(self.conn)
        if not habits:
            self.summary.setText("No data yet.")
            return
        lines = []
        for h in habits:
            hd = dict(h)
            completions = get_completions(self.conn, int(h["id"]))
            pauses = [(p["start_date"], p["end_date"]) for p in list_pauses(self.conn, int(h["id"]))]
            r30 = completion_rate(hd, completions, pauses, today_iso, days=30)
            r90 = completion_rate(hd, completions, pauses, today_iso, days=90)
            rall = completion_rate(hd, completions, pauses, today_iso, days=365 * 3)
            best = best_streak(hd, completions, pauses, today_iso)
            cur = current_streak(hd, completions, pauses, today_iso)
            lab = QLabel(
                f"{h['name']}: 30d {r30:.0%} | 90d {r90:.0%} | all {rall:.0%} | "
                f"streak {cur} | best {best}"
            )
            self.layout.addWidget(lab)
            self.rows.append(lab)
            lines.append(f"{h['name']} {r30:.2f} {best}")
        self.summary.setText(f"{len(habits)} habits tracked.")
