"""Main window — S09-3: Today cards with one-tap check-off."""

from __future__ import annotations

import sqlite3
from datetime import date

from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.schedule import is_due
from core.streak import current_streak, is_done
from db.store import (
    create_habit,
    get_completions,
    init_db,
    list_habits,
    log_completion,
)
from ui.add_dialog import AddHabitDialog
from ui.cards import HabitCard


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
        self.cards_box = QVBoxLayout()
        cards_host = QWidget()
        cards_host.setLayout(self.cards_box)
        self.empty_label = QLabel("No habits yet. Add your first habit.")
        today_layout.addWidget(cards_host)
        today_layout.addWidget(self.empty_label)
        self.add_button = QPushButton("Add habit")
        self.add_button.clicked.connect(self._on_add)
        today_layout.addWidget(self.add_button)
        self.today_cards: list[HabitCard] = []
        self.tabs.addTab(self.today_page, "Today")
        self.tabs.addTab(_placeholder("List — coming in S14."), "List")
        self.tabs.addTab(_placeholder("Grid — coming in S10."), "Grid")
        self.tabs.addTab(_placeholder("Stats — coming in S15."), "Stats")
        self.refresh_today()

    def _clear_cards(self) -> None:
        for card in self.today_cards:
            self.cards_box.removeWidget(card)
            card.deleteLater()
        self.today_cards = []

    def refresh_today(self, today: str | None = None) -> None:
        today_iso = today or date.today().isoformat()
        self._clear_cards()
        habits = [h for h in list_habits(self.conn) if is_due(dict(h), today_iso)]
        self.empty_label.setVisible(not habits)
        for h in habits:
            hd = dict(h)
            completions = get_completions(self.conn, int(h["id"]))
            has_row = today_iso in completions
            done = is_done(hd, completions.get(today_iso), has_row)
            counter_text = ""
            if hd.get("type") == "counter":
                counter_text = f"{int(completions.get(today_iso, 0))}/{int(hd.get('target_count', 1))}"
            streak = current_streak(hd, completions, [], today_iso)
            card = HabitCard(
                int(h["id"]),
                str(h["name"]),
                on_tap=self._on_tap,
                counter_text=counter_text,
                streak_active=streak > 0,
                done=done,
            )
            self.cards_box.addWidget(card)
            self.today_cards.append(card)

    def _on_tap(self, habit_id: int) -> None:
        today_iso = date.today().isoformat()
        row = self.conn.execute("SELECT * FROM habits WHERE id=?", (habit_id,)).fetchone()
        if row is None:
            return
        hd = dict(row)
        completions = get_completions(self.conn, habit_id)
        current = int(completions.get(today_iso, 0))
        if hd.get("type") == "counter":
            new_value = current + 1
        else:
            new_value = 1  # yes_no check-off; dont_do slip (MVP)
        log_completion(self.conn, habit_id, today_iso, new_value)
        self.refresh_today()

    def _on_add(self) -> None:
        dlg = AddHabitDialog(self)
        if dlg.exec():
            try:
                create_habit(self.conn, **dlg.values())
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid habit", str(exc))
                return
            self.refresh_today()
