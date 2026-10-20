"""Detail dialog — S13-2: retro edit + pause range."""

from __future__ import annotations

import sqlite3

from PySide6.QtCore import QDate
from PySide6.QtGui import QBrush, QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from core.heatmap import build_matrix
from core.streak import best_streak, current_streak, is_done, is_paused
from db.store import (
    add_pause, clear_completion, delete_habit, get_completion,
    list_pauses, log_completion, set_archived, update_habit,
)
from ui.add_dialog import AddHabitDialog
from ui.heatmap_widget import HeatmapWidget
from ui.pause_dialog import PauseDialog


class DetailDialog(QDialog):
    def __init__(self, conn: sqlite3.Connection, habit_id: int, parent=None) -> None:
        super().__init__(parent)
        self.conn = conn
        self.habit_id = habit_id
        row = conn.execute("SELECT * FROM habits WHERE id=?", (habit_id,)).fetchone()
        self.habit = dict(row) if row else {}
        self.setWindowTitle(f"Habit — {self.habit.get('name', habit_id)}")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{self.habit.get('name','')} [{self.habit.get('type')}]"))

        self.streak_label = QLabel("")
        layout.addWidget(self.streak_label)
        self.history_heatmap = HeatmapWidget(cell=8, gap=2)
        layout.addWidget(self.history_heatmap)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self._load_day)
        layout.addWidget(self.calendar)

        self.info = QLabel("")
        layout.addWidget(self.info)

        mid = QHBoxLayout()
        self.value_spin = QSpinBox()
        self.value_spin.setRange(0, 1000)
        self.value_spin.setValue(1)
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("note (optional)")
        mid.addWidget(QLabel("Value"))
        mid.addWidget(self.value_spin)
        mid.addWidget(self.note_edit)
        layout.addLayout(mid)

        btns = QHBoxLayout()
        self.save_button = QPushButton("Save day")
        self.save_button.clicked.connect(self.save_day)
        self.clear_button = QPushButton("Clear day")
        self.clear_button.clicked.connect(self.clear_day)
        self.pause_button = QPushButton("Pause…")
        self.pause_button.clicked.connect(self.pause_range)
        self.edit_button = QPushButton("Edit…")
        self.edit_button.clicked.connect(self.edit_habit)
        self.archive_button = QPushButton("Archive")
        self.archive_button.clicked.connect(self.toggle_archive)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_habit)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        btns.addWidget(self.save_button)
        btns.addWidget(self.clear_button)
        btns.addWidget(self.pause_button)
        layout.addLayout(btns)
        meta = QHBoxLayout()
        meta.addWidget(self.edit_button)
        meta.addWidget(self.archive_button)
        meta.addWidget(self.delete_button)
        meta.addWidget(close_button)
        layout.addLayout(meta)
        self.pause_info = QLabel("")
        layout.addWidget(self.pause_info)
        self._load_day()
        self._load_pauses()
        self._highlight_days()
        self._refresh_history()
        self._reload_habit()

    def selected_iso(self) -> str:
        return self.calendar.selectedDate().toString("yyyy-MM-dd")

    def _load_day(self) -> None:
        iso = self.selected_iso()
        row = get_completion(self.conn, self.habit_id, iso)
        if row is None:
            self.info.setText(f"{iso}: —")
            self.value_spin.setValue(1)
            self.note_edit.setText("")
        else:
            self.info.setText(f"{iso}: value={row['value']} note={row['note']!r}")
            self.value_spin.setValue(int(row["value"]))
            self.note_edit.setText(row["note"] or "")

    def _highlight_days(self) -> None:
        """Paint done days green and paused days gray, like HabitForge detail."""
        from db.store import get_completions

        completions = get_completions(self.conn, self.habit_id)
        pauses = [(p["start_date"], p["end_date"]) for p in list_pauses(self.conn, self.habit_id)]
        done_fmt = QTextCharFormat()
        done_fmt.setBackground(QBrush(QColor("#30a14e")))
        done_fmt.setForeground(QBrush(QColor("#ffffff")))
        pause_fmt = QTextCharFormat()
        pause_fmt.setBackground(QBrush(QColor("#414868")))
        pause_fmt.setForeground(QBrush(QColor("#a9b1d6")))
        seen: set[str] = set()
        for iso, val in completions.items():
            if iso in seen:
                continue
            seen.add(iso)
            if is_done(self.habit, val, True):
                self.calendar.setDateTextFormat(QDate.fromString(iso, "yyyy-MM-dd"), done_fmt)
        for p in list_pauses(self.conn, self.habit_id):
            s = QDate.fromString(p["start_date"], "yyyy-MM-dd")
            e = QDate.fromString(p["end_date"], "yyyy-MM-dd")
            d = s
            while d <= e:
                if d.toString("yyyy-MM-dd") not in completions:
                    self.calendar.setDateTextFormat(d, pause_fmt)
                d = d.addDays(1)

    def _refresh_history(self) -> None:
        """Streak line + 120-day mini heatmap, like HabitForge detail."""
        from datetime import date as _d

        from db.store import get_completions

        completions = get_completions(self.conn, self.habit_id)
        pauses = [(p["start_date"], p["end_date"]) for p in list_pauses(self.conn, self.habit_id)]
        today = _d.today().isoformat()
        cur = current_streak(self.habit, completions, pauses, today)
        best = best_streak(self.habit, completions, pauses, today)
        fire = "🔥 " if cur > 0 else ""
        self.streak_label.setText(f"{fire}Streak {cur} — best {best}")
        target = int(self.habit.get("target_count", 1) or 1)
        self.history_heatmap.set_matrix(
            build_matrix(completions, end_date=today, days=120, target=target)
        )

    def save_day(self) -> None:
        log_completion(
            self.conn, self.habit_id, self.selected_iso(),
            int(self.value_spin.value()), self.note_edit.text(),
        )
        self._load_day()
        self._highlight_days()
        self._refresh_history()

    def clear_day(self) -> None:
        clear_completion(self.conn, self.habit_id, self.selected_iso())
        self._load_day()
        self._highlight_days()
        self._refresh_history()

    def _reload_habit(self) -> None:
        row = self.conn.execute("SELECT * FROM habits WHERE id=?", (self.habit_id,)).fetchone()
        self.habit = dict(row) if row else {}
        self.setWindowTitle(f"Habit — {self.habit.get('name', self.habit_id)}")
        archived = bool(self.habit.get("archived", 0))
        self.archive_button.setText("Unarchive" if archived else "Archive")

    def edit_habit(self) -> None:
        dlg = AddHabitDialog(self)
        dlg.set_values(self.habit)
        if dlg.exec():
            try:
                vals = dlg.values()
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid habit", str(exc))
                return
            update_habit(
                self.conn, self.habit_id,
                name=vals["name"], type=vals["habit_type"],
                target_count=vals["target_count"],
                schedule_type=vals["schedule_type"],
                schedule_json=vals["schedule_json"],
            )
            self._reload_habit()
            self._highlight_days()
            self._refresh_history()

    def toggle_archive(self) -> None:
        set_archived(self.conn, self.habit_id, not self.habit.get("archived", 0))
        self.accept()

    def delete_habit(self) -> None:
        if QMessageBox.question(self, "Delete habit",
                               f"Delete '{self.habit.get('name')}' and all its history?") != QMessageBox.Yes:
            return
        delete_habit(self.conn, self.habit_id)
        self.accept()

    def _load_pauses(self) -> None:
        pauses = list_pauses(self.conn, self.habit_id)
        if not pauses:
            self.pause_info.setText("No pauses.")
            return
        pretty = ", ".join(f"{p['start_date']}→{p['end_date']}" for p in pauses[-3:])
        self.pause_info.setText(f"Pauses: {pretty}")

    def pause_range(self) -> None:
        dlg = PauseDialog(self)
        if dlg.exec():
            try:
                vals = dlg.values()
                add_pause(self.conn, self.habit_id, **vals)
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid pause", str(exc))
                return
            self._load_pauses()
            self._highlight_days()
