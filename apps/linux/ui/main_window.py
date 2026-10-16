"""Main window — S07-1: 4-tab shell, Today empty state. No DB yet."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget


def _placeholder(text: str) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.addWidget(QLabel(text))
    layout.addStretch(1)
    return page


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("StreakGrid")
        self.resize(900, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.today_page = _placeholder("Today — no habits yet. Add your first habit.")
        self.tabs.addTab(self.today_page, "Today")
        self.tabs.addTab(_placeholder("List — coming in S14."), "List")
        self.tabs.addTab(_placeholder("Grid — coming in S10."), "Grid")
        self.tabs.addTab(_placeholder("Stats — coming in S15."), "Stats")
