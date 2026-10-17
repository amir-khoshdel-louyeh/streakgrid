"""Habit card — S11-3: tap + details buttons."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy


class HabitCard(QFrame):
    """Single habit row. `on_tap(id)` check-off, `on_open(id)` detail dialog."""

    def __init__(
        self,
        habit_id: int,
        name: str,
        on_tap=None,
        on_open=None,
        counter_text: str = "",
        streak_active: bool = False,
        done: bool = False,
        folder_tag: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.habit_id = habit_id
        self._on_tap = on_tap
        self._on_open = on_open
        self._base_name = name
        self._counter_text = counter_text
        self._streak_active = streak_active
        self._folder_tag = folder_tag
        self.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(self)
        self.name_label = QLabel()
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.detail_button = QPushButton("📅")
        self.detail_button.setFixedSize(36, 36)
        self.detail_button.clicked.connect(self._handle_open)
        self.tap_button = QPushButton("●" if done else "○")
        self.tap_button.setFixedSize(40, 40)
        self.tap_button.setStyleSheet("font-size: 20px; border-radius: 20px;")
        self.tap_button.clicked.connect(self._handle_tap)
        layout.addWidget(self.name_label)
        layout.addWidget(self.detail_button)
        layout.addWidget(self.tap_button)
        self._render_name()

    def _render_name(self) -> None:
        prefix = "🔥 " if self._streak_active else ""
        suffix = f"  {self._counter_text}" if self._counter_text else ""
        folder = f" [{self._folder_tag}]" if self._folder_tag else ""
        self.name_label.setText(f"{prefix}{self._base_name}{suffix}{folder}")

    def _handle_tap(self) -> None:
        if self._on_tap is not None:
            self._on_tap(self.habit_id)

    def _handle_open(self) -> None:
        if self._on_open is not None:
            self._on_open(self.habit_id)

    def set_done(self, done: bool) -> None:
        self.tap_button.setText("●" if done else "○")

    def set_counter(self, text: str) -> None:
        self._counter_text = text
        self._render_name()

    def set_streak(self, active: bool) -> None:
        self._streak_active = active
        self._render_name()
