"""Nag mode — S18-1: periodic pending check (QTimer skeleton)."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import date

from PySide6.QtCore import QObject, QTimer

from core.schedule import is_due
from core.streak import is_done, is_paused
from db.store import get_completions, list_habits, list_pauses


def find_pending(conn: sqlite3.Connection, today_iso: str | None = None) -> list[dict]:
    """Due-undone habits today (pauses respected)."""
    today_iso = today_iso or date.today().isoformat()
    out: list[dict] = []
    for h in list_habits(conn):
        hd = dict(h)
        if not is_due(hd, today_iso):
            continue
        pauses = [(p["start_date"], p["end_date"]) for p in list_pauses(conn, int(h["id"]))]
        if is_paused(pauses, today_iso):
            continue
        comp = get_completions(conn, int(h["id"]))
        if not is_done(hd, comp.get(today_iso), today_iso in comp):
            out.append(hd)
    return out


class NagService(QObject):
    def __init__(
        self,
        conn: sqlite3.Connection,
        interval_min: int = 15,
        notify: Callable[[str, str], None] | None = None,
        is_snoozed: Callable[[], bool] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.conn = conn
        self.notify = notify or (lambda _t, _b: None)
        self.is_snoozed = is_snoozed or (lambda: False)
        self.timer = QTimer(self)
        self.timer.setInterval(int(interval_min * 60 * 1000))
        self.timer.timeout.connect(self.tick)

    def start(self) -> None:
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()

    def tick(self) -> list[dict]:
        """Notify (critical) while pending; silent once all done or snoozed."""
        if self.is_snoozed():
            return []
        pending = find_pending(self.conn)
        if pending:
            names = ", ".join(h.get("name", "?") for h in pending[:3])
            self.notify(f"{len(pending)} habits due", names or "Time for habits!")
        return pending
