"""Habit card — S09-2: name + circular one-tap button."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy


class HabitCard(QFrame):
    """Single habit row. Emits tap via `on_tap` callback(id)."""

    def __init__(self, habit_id: int, name: str, on_tap=None, parent=None) -> None:
        super().__init__(parent)
        self.habit_id = habit_id
        self._on_tap = on_tap
        self.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(self)
        self.name_label = QLabel(name)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.tap_button = QPushButton("○")
        self.tap_button.setFixedSize(40, 40)
        self.tap_button.setStyleSheet("font-size: 20px; border-radius: 20px;")
        self.tap_button.clicked.connect(self._handle_tap)
        layout.addWidget(self.name_label)
        layout.addWidget(self.tap_button)

    def _handle_tap(self) -> None:
        if self._on_tap is not None:
            self._on_tap(self.habit_id)

    def set_done(self, done: bool) -> None:
        self.tap_button.setText("●" if done else "○")
