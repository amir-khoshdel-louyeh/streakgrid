"""Desktop widget — S19-1: frameless shell + drag + saved position."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import QSettings


class DesktopWidget(QWidget):
    SETTINGS_ORG = "StreakGrid"
    SETTINGS_APP = "DesktopWidget"

    def __init__(self, parent=None) -> None:
        super().__init__(
            parent,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool,
        )
        self.setWindowTitle("StreakGrid Widget")
        self._drag_offset: QPoint | None = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("StreakGrid — Today"))
        self._restore_position()

    def _settings(self) -> QSettings:
        return QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

    def _restore_position(self) -> None:
        pos = self._settings().value("pos")
        if pos is not None:
            try:
                self.move(pos)
            except (TypeError, AttributeError):
                pass

    def _save_position(self) -> None:
        self._settings().setValue("pos", self.pos())

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_offset = None
        self._save_position()
        super().mouseReleaseEvent(event)

    @staticmethod
    def can_pin() -> bool:
        """False on Wayland compositors that ignore always-on-top (fallback: tray)."""
        import os

        from PySide6.QtGui import QGuiApplication

        platform = ""
        try:
            platform = (QGuiApplication.platformName() or "").lower()
        except RuntimeError:
            pass
        if "wayland" in platform or "wayland" in os.environ.get("XDG_SESSION_TYPE", "").lower():
            return False
        return True
