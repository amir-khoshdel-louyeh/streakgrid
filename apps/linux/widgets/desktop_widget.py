"""Desktop widget — S19-2: one-tap check-off without main window."""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Callable

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import QSettings

from core.schedule import is_due
from core.streak import is_done
from db.store import get_completions, list_habits, log_completion


class DesktopWidget(QWidget):
    SETTINGS_ORG = "StreakGrid"
    SETTINGS_APP = "DesktopWidget"

    def __init__(
        self,
        conn: sqlite3.Connection | None = None,
        on_check: Callable[[int], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(
            parent,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool,
        )
        self.setWindowTitle("StreakGrid Widget")
        self.conn = conn
        self._on_check = on_check
        self._drag_offset: QPoint | None = None
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("StreakGrid — Today"))
        self.rows: list[QWidget] = []
        self._restore_position()
        if not self.can_pin():
            # Wayland-safe fallback: tray quick menu already covers check-off.
            self.setToolTip("Compositor blocks pinning — use tray menu.")

    def _settings(self) -> QSettings:
        return QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

    def _restore_position(self) -> None:
        pos = self._settings().value("pos")
        if pos is not None:
            try:
                self.move(pos)
            except (TypeError, AttributeError):
                pass

    def _save_position(self) -> None:
        self._settings().setValue("pos", self.pos())

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_offset = None
        self._save_position()
        super().mouseReleaseEvent(event)

    def refresh(self, today_iso: str | None = None) -> int:
        """Rebuild due-today rows. Returns row count. No main window needed."""
        for r in self.rows:
            self.layout.removeWidget(r)
            r.deleteLater()
        self.rows = []
        if self.conn is None:
            return 0
        today_iso = today_iso or date.today().isoformat()
        n = 0
        for h in list_habits(self.conn):
            hd = dict(h)
            if not is_due(hd, today_iso):
                continue
            comp = get_completions(self.conn, int(h["id"]))
            done = is_done(hd, comp.get(today_iso), today_iso in comp)
            row = QWidget()
            box = QHBoxLayout(row)
            box.setContentsMargins(0, 0, 0, 0)
            box.addWidget(QLabel(str(h["name"])))
            btn = QPushButton("●" if done else "○")
            btn.setFixedSize(32, 32)
            btn.clicked.connect(lambda _c, hid=int(h["id"]): self.check(hid))
            box.addWidget(btn)
            self.layout.addWidget(row)
            self.rows.append(row)
            n += 1
        return n

    def check(self, habit_id: int) -> None:
        """One-tap check-off straight into SQLite."""
        if self._on_check is not None:
            self._on_check(habit_id)
            self.refresh()
            return
        if self.conn is None:
            return
        today_iso = date.today().isoformat()
        row = self.conn.execute("SELECT * FROM habits WHERE id=?", (habit_id,)).fetchone()
        if row is None:
            return
        hd = dict(row)
        comp = get_completions(self.conn, habit_id)
        new_value = int(comp.get(today_iso, 0)) + 1 if hd.get("type") == "counter" else 1
        log_completion(self.conn, habit_id, today_iso, new_value)
        self.refresh()

    @staticmethod
    def can_pin() -> bool:
        """False on Wayland compositors that ignore always-on-top (fallback: tray)."""
        import os

        from PySide6.QtGui import QGuiApplication

        platform = ""
        try:
            platform = (QGuiApplication.platformName() or "").lower()
        except RuntimeError:
            pass
        if "wayland" in platform or "wayland" in os.environ.get("XDG_SESSION_TYPE", "").lower():
            return False
        return True
