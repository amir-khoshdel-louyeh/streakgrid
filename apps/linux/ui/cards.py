"""Habit card — S09-3: counter text + streak fire."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy


class HabitCard(QFrame):
    """Single habit row. Emits tap via `on_tap` callback(id)."""

    def __init__(
        self,
        habit_id: int,
        name: str,
        on_tap=None,
        counter_text: str = "",
        streak_active: bool = False,
        done: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.habit_id = habit_id
        self._on_tap = on_tap
        self._base_name = name
        self._counter_text = counter_text
        self._streak_active = streak_active
        self.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(self)
        self.name_label = QLabel()
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.tap_button = QPushButton("●" if done else "○")
        self.tap_button.setFixedSize(40, 40)
        self.tap_button.setStyleSheet("font-size: 20px; border-radius: 20px;")
        self.tap_button.clicked.connect(self._handle_tap)
        layout.addWidget(self.name_label)
        layout.addWidget(self.tap_button)
        self._render_name()

    def _render_name(self) -> None:
        prefix = "🔥 " if self._streak_active else ""
        suffix = f"  {self._counter_text}" if self._counter_text else ""
        self.name_label.setText(f"{prefix}{self._base_name}{suffix}")

    def _handle_tap(self) -> None:
        if self._on_tap is not None:
            self._on_tap(self.habit_id)

    def set_done(self, done: bool) -> None:
        self.tap_button.setText("●" if done else "○")

    def set_counter(self, text: str) -> None:
        self._counter_text = text
        self._render_name()

    def set_streak(self, active: bool) -> None:
        self._streak_active = active
        self._render_name()
