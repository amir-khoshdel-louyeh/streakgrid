"""Detail dialog — S11-2: calendar + note + tick/untick (retroactive edit)."""

from __future__ import annotations

import sqlite3

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from db.store import clear_completion, get_completion, log_completion


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
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        btns.addWidget(self.save_button)
        btns.addWidget(self.clear_button)
        btns.addWidget(close_button)
        layout.addLayout(btns)
        self._load_day()

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

    def save_day(self) -> None:
        log_completion(
            self.conn, self.habit_id, self.selected_iso(),
            int(self.value_spin.value()), self.note_edit.text(),
        )
        self._load_day()

    def clear_day(self) -> None:
        clear_completion(self.conn, self.habit_id, self.selected_iso())
        self._load_day()
