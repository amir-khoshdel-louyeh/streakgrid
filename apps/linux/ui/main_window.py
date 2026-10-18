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
from ui.list_view import ListView


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
        self.list_view = ListView(self.conn)
        self.tabs.addTab(self.list_view, "List")
        self.grid_page = QWidget()
        grid_layout = QVBoxLayout(self.grid_page)
        self.grid_selector = QComboBox()
        self.grid_selector.currentIndexChanged.connect(lambda _i: self.refresh_grid())
        self.grid_heatmap = HeatmapWidget(cell=14, gap=3)
        self.export_button = QPushButton("Export PNG")
        self.export_button.clicked.connect(self._on_export_grid)
        grid_layout.addWidget(self.grid_selector)
        grid_layout.addWidget(self.grid_heatmap)
        grid_layout.addWidget(self.export_button)
        grid_layout.addStretch(1)
        self.tabs.addTab(self.grid_page, "Grid")
        self.tabs.addTab(_placeholder("Stats — coming in S15."), "Stats")
        self._folder_ids: list[int | None] = [None]
        self.refresh_folders()
        self.refresh_all()

    def refresh_all(self) -> None:
        self.refresh_today()
        self.refresh_grid()
        if hasattr(self, "list_view"):
            self.list_view.refresh()
        if hasattr(self, "stats_label"):
            self.refresh_stats()

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
        self.refresh_all()

    def _on_open_detail(self, habit_id: int) -> None:
        dlg = DetailDialog(self.conn, habit_id, self)
        dlg.exec()
        self.refresh_all()

    def refresh_grid(self, today: str | None = None) -> None:
        """S14: full 365-day grid for selected habit."""
        from pathlib import Path

        today_iso = today or date.today().isoformat()
        habits = list_habits(self.conn)
        current_id = self.grid_selector.currentData()
        self.grid_selector.blockSignals(True)
        self.grid_selector.clear()
        for h in habits:
            self.grid_selector.addItem(str(h["name"]), int(h["id"]))
        if habits and current_id in [int(h["id"]) for h in habits]:
            idx = [int(h["id"]) for h in habits].index(int(current_id))
            self.grid_selector.setCurrentIndex(idx)
        self.grid_selector.blockSignals(False)
        if not habits:
            self.grid_heatmap.set_matrix([[0] * 7 for _ in range(53)])
            return
        sel = int(self.grid_selector.currentData() or habits[0]["id"])
        row = self.conn.execute("SELECT * FROM habits WHERE id=?", (sel,)).fetchone()
        hd = dict(row)
        completions = get_completions(self.conn, sel)
        target = int(hd.get("target_count", 1) or 1)
        self.grid_heatmap.set_matrix(
            build_matrix(completions, end_date=today_iso, days=365, target=target)
        )

    def export_grid_png(self, out_dir: str | None = None) -> str:
        """Export current grid widget to ~/Pictures/streakgrid-YYYY-MM-DD.png (S14 DoD)."""
        from pathlib import Path

        today_iso = date.today().isoformat()
        base = Path(out_dir) if out_dir else Path.home() / "Pictures"
        base.mkdir(parents=True, exist_ok=True)
        path = str(base / f"streakgrid-{today_iso}.png")
        self.grid_heatmap.grab().save(path)
        return path

    def _on_export_grid(self) -> None:
        path = self.export_grid_png()
        QMessageBox.information(self, "Exported", f"Saved {path}")

    def _on_add(self) -> None:
        dlg = AddHabitDialog(self)
        if dlg.exec():
            try:
                create_habit(self.conn, **dlg.values())
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid habit", str(exc))
                return
            self.refresh_folders()
            self.refresh_all()
