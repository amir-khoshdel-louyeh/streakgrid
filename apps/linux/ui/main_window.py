"""Main window — S10-2: Grid shows sample habit heatmap."""

from __future__ import annotations

import sqlite3
from datetime import date

from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.heatmap import build_matrix
from core.schedule import is_due
from core.streak import current_streak, is_done
from db.store import (
    create_folder,
    create_habit,
    get_completions,
    init_db,
    list_folders,
    list_habits,
    list_pauses,
    log_completion,
)
from ui.add_dialog import AddHabitDialog
from ui.cards import HabitCard
from ui.detail_dialog import DetailDialog
from ui.heatmap_widget import HeatmapWidget


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
        self.folder_filter = QComboBox()
        self.folder_filter.currentIndexChanged.connect(lambda _i: self.refresh_today())
        today_layout.addWidget(self.folder_filter)
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
        self.grid_page = QWidget()
        grid_layout = QVBoxLayout(self.grid_page)
        self.grid_label = QLabel("Grid — no habits yet.")
        self.grid_heatmap = HeatmapWidget()
        grid_layout.addWidget(self.grid_label)
        grid_layout.addWidget(self.grid_heatmap)
        grid_layout.addStretch(1)
        self.tabs.addTab(self.grid_page, "Grid")
        self.tabs.addTab(_placeholder("Stats — coming in S15."), "Stats")
        self._folder_ids: list[int | None] = [None]
        self.refresh_folders()
        self.refresh_today()
        self.refresh_grid()

    def refresh_folders(self) -> None:
        current = self.folder_filter.currentData() if hasattr(self, "folder_filter") else None
        self.folder_filter.blockSignals(True)
        self.folder_filter.clear()
        self.folder_filter.addItem("All folders", None)
        self._folder_ids = [None]
        for f in list_folders(self.conn):
            self.folder_filter.addItem(f"● {f['name']}", int(f["id"]))
            self._folder_ids.append(int(f["id"]))
        if current in self._folder_ids:
            self.folder_filter.setCurrentIndex(self._folder_ids.index(current))
        self.folder_filter.blockSignals(False)

    def _clear_cards(self) -> None:
        for card in self.today_cards:
            self.cards_box.removeWidget(card)
            card.deleteLater()
        self.today_cards = []

    def refresh_today(self, today: str | None = None) -> None:
        today_iso = today or date.today().isoformat()
        self._clear_cards()
        wanted = self.folder_filter.currentData() if hasattr(self, "folder_filter") else None
        folders = {int(f["id"]): dict(f) for f in list_folders(self.conn)}
        habits = [h for h in list_habits(self.conn) if is_due(dict(h), today_iso)]
        if wanted is not None:
            habits = [h for h in habits if h["folder_id"] == wanted]
        self.empty_label.setVisible(not habits)
        for h in habits:
            hd = dict(h)
            completions = get_completions(self.conn, int(h["id"]))
            pauses = [(p["start_date"], p["end_date"]) for p in list_pauses(self.conn, int(h["id"]))]
            has_row = today_iso in completions
            done = is_done(hd, completions.get(today_iso), has_row)
            counter_text = ""
            if hd.get("type") == "counter":
                counter_text = f"{int(completions.get(today_iso, 0))}/{int(hd.get('target_count', 1))}"
            streak = current_streak(hd, completions, pauses, today_iso)
            folder_tag = ""
            if hd.get("folder_id") in folders:
                folder_tag = str(folders[int(hd["folder_id"])]["name"])
            card = HabitCard(
                int(h["id"]),
                str(h["name"]),
                on_tap=self._on_tap,
                on_open=self._on_open_detail,
                counter_text=counter_text,
                streak_active=streak > 0,
                done=done,
                folder_tag=folder_tag,
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
        self.refresh_grid()

    def _on_open_detail(self, habit_id: int) -> None:
        dlg = DetailDialog(self.conn, habit_id, self)
        dlg.exec()
        self.refresh_today()
        self.refresh_grid()

    def refresh_grid(self, today: str | None = None) -> None:
        """S10 DoD: render 1 sample habit's 365-day heatmap."""
        today_iso = today or date.today().isoformat()
        habits = list_habits(self.conn)
        if not habits:
            self.grid_label.setText("Grid — no habits yet.")
            self.grid_heatmap.set_matrix([[0] * 7 for _ in range(53)])
            return
        first = dict(habits[0])
        completions = get_completions(self.conn, int(first["id"]))
        target = int(first.get("target_count", 1) or 1)
        self.grid_label.setText(f"Grid — {first.get('name')}")
        self.grid_heatmap.set_matrix(
            build_matrix(completions, end_date=today_iso, days=365, target=target)
        )

    def _on_add(self) -> None:
        dlg = AddHabitDialog(self)
        if dlg.exec():
            try:
                create_habit(self.conn, **dlg.values())
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid habit", str(exc))
                return
            self.refresh_folders()
            self.refresh_today()
            self.refresh_grid()
