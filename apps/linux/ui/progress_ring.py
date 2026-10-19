"""Progress ring — P1-1: daily done/due ring (like HabitForge today header)."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class ProgressRing(QWidget):
    def __init__(self, parent=None, size: int = 96) -> None:
        super().__init__(parent)
        self._done = 0
        self._total = 0
        self._size = size
        self.setFixedSize(size, size)

    def set_progress(self, done: int, total: int) -> None:
        self._done = max(0, int(done))
        self._total = max(0, int(total))
        self.update()

    def fraction(self) -> float:
        if self._total <= 0:
            return 0.0
        return min(1.0, self._done / self._total)

    def sizeHint(self) -> QSize:
        return QSize(self._size, self._size)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        margin = 8
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        track = QPen(QColor("#414868"), 9)
        track.setCapStyle(Qt.RoundCap)
        painter.setPen(track)
        painter.drawEllipse(rect)
        if self._total > 0:
            done_pen = QPen(QColor("#7aa2f7"), 9)
            done_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(done_pen)
            painter.drawArc(rect, 90 * 16, -int(self.fraction() * 360 * 16))
        painter.setPen(QColor("#c0caf5"))
        painter.setFont(QFont("Sans", 11, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self._done}/{self._total}")
        painter.end()
