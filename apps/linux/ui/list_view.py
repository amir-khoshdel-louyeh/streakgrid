"""List view — S14-1: all habits with mini heatmap + streak."""

from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from core.heatmap import build_matrix
from core.streak import best_streak, current_streak
from db.store import get_completions, list_habits, list_pauses
from ui.heatmap_widget import HeatmapWidget


class ListView(QWidget):
    def __init__(self, conn: sqlite3.Connection, parent=None) -> None:
        super().__init__(parent)
        self.conn = conn
        self.layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search habits…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _t: self.refresh())
        self.layout.addWidget(self.search)
        self.rows: list[QWidget] = []

    def refresh(self, today: str | None = None) -> None:
        from datetime import date

        today_iso = today or date.today().isoformat()
        for r in self.rows:
            self.layout.removeWidget(r)
            r.deleteLater()
        self.rows = []
        habits = list_habits(self.conn, include_archived=True)
        query = self.search.text().strip().lower()
        if query:
            habits = [h for h in habits if query in str(h["name"]).lower()]
        if not habits:
            empty = QLabel("No habits found." if query else "No habits yet.")
            self.layout.addWidget(empty)
            self.rows.append(empty)
            return
        for h in habits:
            hd = dict(h)
            completions = get_completions(self.conn, int(h["id"]))
            pauses = [(p["start_date"], p["end_date"]) for p in list_pauses(self.conn, int(h["id"]))]
            cur = current_streak(hd, completions, pauses, today_iso)
            best = best_streak(hd, completions, pauses, today_iso)
            row = QFrame()
            row.setFrameShape(QFrame.StyledPanel)
            box = QHBoxLayout(row)
            archived_tag = "  [archived]" if h["archived"] else ""
            name = QLabel(f"{h['name']}  🔥{cur}  best {best}{archived_tag}")
            mini = HeatmapWidget(cell=5, gap=2)
            mini.setFixedHeight(5 * 0 + 7 * (5 + 2) + 2)
            mini.set_matrix(
                build_matrix(completions, end_date=today_iso, days=120,
                             target=int(hd.get("target_count", 1) or 1))
            )
            box.addWidget(name, stretch=1)
            box.addWidget(mini)
            self.layout.addWidget(row)
            self.rows.append(row)
