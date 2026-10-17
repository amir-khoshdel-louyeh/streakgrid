"""Mini heatmap — S10-1: 53x7 green grid via paintEvent."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]


class HeatmapWidget(QWidget):
    def __init__(self, parent=None, cell: int = 12, gap: int = 3) -> None:
        super().__init__(parent)
        self._grid: list[list[int]] = [[0] * 7 for _ in range(53)]
        self._cell = cell
        self._gap = gap
        self.setMinimumSize(self.sizeHint())

    def set_matrix(self, grid: list[list[int]]) -> None:
        self._grid = grid
        self.update()

    def matrix(self) -> list[list[int]]:
        return self._grid

    def sizeHint(self) -> QSize:
        w = 53 * (self._cell + self._gap) + self._gap
        h = 7 * (self._cell + self._gap) + self._gap
        return QSize(w, h)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setPen("transparent")
        for col in range(53):
            for row in range(7):
                level = 0
                if col < len(self._grid) and row < len(self._grid[col]):
                    level = max(0, min(4, int(self._grid[col][row])))
                painter.setBrush(QColor(COLORS[level]))
                x = self._gap + col * (self._cell + self._gap)
                y = self._gap + row * (self._cell + self._gap)
                painter.drawRect(x, y, self._cell, self._cell)
        painter.end()
