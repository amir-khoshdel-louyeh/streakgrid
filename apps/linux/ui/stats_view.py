"""Stats view — S15-2: rates + perfect days + weekday chart."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.schedule import is_due
from core.streak import best_streak, completion_rate, current_streak, is_done, is_paused
from db.store import get_completions, list_habits, list_pauses


class StatsView(QWidget):
    def __init__(self, conn: sqlite3.Connection, parent=None) -> None:
        super().__init__(parent)
        self.conn = conn
        self.layout = QVBoxLayout(self)
        self.summary = QLabel("")
        self.layout.addWidget(self.summary)
        self.extra = QLabel("")
        self.layout.addWidget(self.extra)
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
        self.extra.setText(self._extra_text(today_iso))

    def _extra_text(self, today_iso: str) -> str:
        """Perfect days (30d) + best/worst weekday over last 12 weeks."""
        end = date.fromisoformat(today_iso)
        habits = [dict(h) for h in list_habits(self.conn)]
        comp = {int(h["id"]): get_completions(self.conn, int(h["id"])) for h in habits}
        pauses = {
            int(h["id"]): [(p["start_date"], p["end_date"]) for p in list_pauses(self.conn, int(h["id"]))]
            for h in habits
        }
        perfect = 0
        for i in range(30):
            d = end - timedelta(days=i)
            iso = d.isoformat()
            due = [h for h in habits if is_due(h, d) and not is_paused(pauses[int(h["id"])], d)]
            if due and all(is_done(h, comp[int(h["id"])].get(iso), iso in comp[int(h["id"])]) for h in due):
                perfect += 1
        wd_done = [0] * 7
        wd_total = [0] * 7
        for i in range(84):
            d = end - timedelta(days=i)
            wd = d.weekday()
            for h in habits:
                if is_due(h, d) and not is_paused(pauses[int(h["id"])], d):
                    wd_total[wd] += 1
                    iso = d.isoformat()
                    if is_done(h, comp[int(h["id"])].get(iso), iso in comp[int(h["id"])]):
                        wd_done[wd] += 1
        rates = [(wd_done[i] / wd_total[i] if wd_total[i] else 0.0) for i in range(7)]
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        best_i = max(range(7), key=lambda i: rates[i])
        worst_i = min(range(7), key=lambda i: rates[i])
        chart = " ".join(f"{names[i]} {rates[i]:.0%}" for i in range(7))
        return f"Perfect days (30d): {perfect} | best {names[best_i]} | worst {names[worst_i]} | {chart}"
