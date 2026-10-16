"""Main window — S08-3: Today backed by SQLite + add dialog."""

from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from db.store import create_habit, init_db, list_habits
from ui.add_dialog import AddHabitDialog


def _placeholder(text: str) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(text))
    layout.addStretch(1)
    return page


class MainWindow(QMainWindow):
    def __init__(self, conn: sqlite3.Connection | None = None) -> None:
        super().__init__()
        self.setWindowTitle("StreakGrid")
        self.resize(900, 600)
        self.conn = conn or init_db()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.today_page = QWidget()
        today_layout = QVBoxLayout(self.today_page)
        self.today_list = QListWidget()
        self.add_button = QPushButton("Add habit")
        self.add_button.clicked.connect(self._on_add)
        today_layout.addWidget(self.today_list)
        today_layout.addWidget(self.add_button)
        self.tabs.addTab(self.today_page, "Today")
        self.tabs.addTab(_placeholder("List — coming in S14."), "List")
        self.tabs.addTab(_placeholder("Grid — coming in S10."), "Grid")
        self.tabs.addTab(_placeholder("Stats — coming in S15."), "Stats")
        self.refresh_today()

    def refresh_today(self) -> None:
        self.today_list.clear()
        habits = list_habits(self.conn)
        if not habits:
            self.today_list.addItem("No habits yet. Add your first habit.")
            return
        for h in habits:
            self.today_list.addItem(f"{h['name']} [{h['type']}/{h['schedule_type']}]")

    def _on_add(self) -> None:
        dlg = AddHabitDialog(self)
        if dlg.exec():
            try:
                create_habit(self.conn, **dlg.values())
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid habit", str(exc))
                return
            self.refresh_today()
