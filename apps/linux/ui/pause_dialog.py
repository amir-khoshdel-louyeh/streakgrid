"""Pause dialog — S13-2: pick a date range to pause a habit."""

from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
)


class PauseDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pause habit")
        self.start_edit = QDateEdit(QDate.currentDate().addDays(-7))
        self.start_edit.setCalendarPopup(True)
        self.end_edit = QDateEdit(QDate.currentDate())
        self.end_edit.setCalendarPopup(True)
        self.reason_edit = QLineEdit()
        self.reason_edit.setPlaceholderText("reason (optional)")

        form = QFormLayout(self)
        form.addRow("Start", self.start_edit)
        form.addRow("End", self.end_edit)
        form.addRow("Reason", self.reason_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict:
        start = self.start_edit.date().toString("yyyy-MM-dd")
        end = self.end_edit.date().toString("yyyy-MM-dd")
        if start > end:
            raise ValueError("pause start must be <= end")
        return {"start_date": start, "end_date": end, "reason": self.reason_edit.text()}
