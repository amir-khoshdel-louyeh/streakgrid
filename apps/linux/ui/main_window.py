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

from core.achievements import ACHIEVEMENTS, check_unlocks, unlock
from core.heatmap import build_matrix
from core.schedule import is_due
from core.streak import current_streak, is_done, is_paused
from services.nag import NagService
from services.tray import add_quick_actions, create_tray, minimize_to_tray
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
from ui.achievements_dialog import AchievementsDialog
from ui.add_dialog import AddHabitDialog
from ui.cards import HabitCard
from ui.detail_dialog import DetailDialog
from ui.heatmap_widget import HeatmapWidget
from ui.list_view import ListView
from ui.stats_view import StatsView


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
        self.achv_button = QPushButton("🏆 Achievements")
        self.achv_button.clicked.connect(self._on_show_achievements)
        today_layout.addWidget(self.add_button)
        today_layout.addWidget(self.achv_button)
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
        self.stats_view = StatsView(self.conn)
        self.tabs.addTab(self.stats_view, "Stats")
        self._folder_ids: list[int | None] = [None]
        self.refresh_folders()
        self.tray = create_tray(self, on_show=self._show_from_tray, on_quit=self._quit_from_tray)
        self._force_quit = False
        self.snoozed_until = None
        add_quick_actions(self.tray, on_done=self._on_tray_done, on_snooze=self._on_tray_snooze)
        from datetime import datetime as _dt

        from services.notify import send as _send

        self.nag = NagService(
            self.conn,
            interval_min=15,
            notify=lambda t, b: _send(t, b, urgency="critical"),
            is_snoozed=lambda: self.snoozed_until is not None
            and _dt.now() < self.snoozed_until,
        )
        self.nag.start()
        self.refresh_all()

    def _show_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _quit_from_tray(self) -> None:
        self._force_quit = True
        self.close()

    def _on_tray_done(self) -> None:
        """Complete first due-undone habit today (tray quick action)."""
        from datetime import date as _d

        today_iso = _d.today().isoformat()
        for h in list_habits(self.conn):
            hd = dict(h)
            if not is_due(hd, today_iso):
                continue
            comp = get_completions(self.conn, int(h["id"]))
            if not is_done(hd, comp.get(today_iso), today_iso in comp):
                self._on_tap(int(h["id"]))
                return

    def _on_tray_snooze(self) -> None:
        from datetime import datetime, timedelta

        self.snoozed_until = datetime.now() + timedelta(minutes=15)

    def closeEvent(self, event) -> None:  # noqa: N802
        if not self._force_quit and minimize_to_tray(self, self.tray, event):
            return
        super().closeEvent(event)

    def refresh_all(self) -> None:
        self.refresh_today()
        self.refresh_grid()
        if hasattr(self, "list_view"):
            self.list_view.refresh()
        if hasattr(self, "stats_view"):
            self.stats_view.refresh()

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
        self.check_achievements(show_banner=True)

    def _on_open_detail(self, habit_id: int) -> None:
        dlg = DetailDialog(self.conn, habit_id, self)
        dlg.exec()
        self.refresh_all()
        self.check_achievements(show_banner=True)

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
            self.check_achievements(show_banner=False)

    def _achievement_inputs(self, today_iso: str) -> dict:
        from datetime import timedelta

        end = date.fromisoformat(today_iso)
        habits = [dict(h) for h in list_habits(self.conn)]
        total = int(self.conn.execute("SELECT COUNT(*) FROM completions").fetchone()[0])
        best_cur = 0
        done7_ids: set[int] = set()
        for h in habits:
            comp = get_completions(self.conn, int(h["id"]))
            pauses = [(p["start_date"], p["end_date"]) for p in list_pauses(self.conn, int(h["id"]))]
            best_cur = max(best_cur, current_streak(dict(h), comp, pauses, today_iso))
            for i in range(7):
                d = (end - timedelta(days=i)).isoformat()
                due = is_due(dict(h), d) and not is_paused(pauses, d)
                if due and is_done(dict(h), comp.get(d), d in comp):
                    done7_ids.add(int(h["id"]))
                    break
        perfect = False
        for i in range(30):
            d = (end - timedelta(days=i)).isoformat()
            due = [
                h for h in habits
                if is_due(h, d) and not is_paused(
                    [(p["start_date"], p["end_date"]) for p in list_pauses(self.conn, int(h["id"]))], d
                )
            ]
            if due:
                ok = True
                for h in due:
                    comp = get_completions(self.conn, int(h["id"]))
                    if not is_done(h, comp.get(d), d in comp):
                        ok = False
                        break
                if ok:
                    perfect = True
                    break
        return {
            "total_completions": total,
            "best_current_streak": best_cur,
            "habits_done_last_7d": len(done7_ids),
            "has_perfect_day": perfect,
        }

    def check_achievements(self, show_banner: bool = True) -> list[str]:
        """Unlock newly earned achievements, persist + banner (S16 DoD)."""
        inputs = self._achievement_inputs(date.today().isoformat())
        fresh = []
        for code in check_unlocks(**inputs):
            if unlock(self.conn, code):
                fresh.append(code)
        if fresh and show_banner:
            names = ", ".join(ACHIEVEMENTS[c] for c in fresh)
            QMessageBox.information(self, "Achievement unlocked!", f"🏅 {names}")
        return fresh

    def _on_show_achievements(self) -> None:
        AchievementsDialog(self.conn, self).exec()
