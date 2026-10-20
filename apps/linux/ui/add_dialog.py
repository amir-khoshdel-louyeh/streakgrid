"""Add-habit dialog — S08-2: name/type/target/schedule form."""

from __future__ import annotations

import json
from datetime import date

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
)


class AddHabitDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New habit")

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Read 20 min")
        self.type_box = QComboBox()
        self.type_box.addItems(["yes_no", "counter", "dont_do"])
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 1000)
        self.target_spin.setValue(1)
        self.schedule_box = QComboBox()
        self.schedule_box.addItems(
            ["daily", "weekly_days", "interval", "times_per_week", "times_per_month"]
        )
        self.detail_edit = QLineEdit()
        self.detail_edit.setPlaceholderText("weekly: 1,3,5 | interval: 3 | times: 3 | else empty")

        form = QFormLayout(self)
        form.addRow("Name", self.name_edit)
        form.addRow("Type", self.type_box)
        form.addRow("Target", self.target_spin)
        form.addRow("Schedule", self.schedule_box)
        form.addRow("Detail", self.detail_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def set_values(self, habit: dict) -> None:
        """Prefill form from a habit row (for editing, U1)."""
        self.setWindowTitle(f"Edit habit — {habit.get('name', '')}")
        self.name_edit.setText(str(habit.get("name", "")))
        self.type_box.setCurrentText(str(habit.get("type", "yes_no")))
        self.target_spin.setValue(int(habit.get("target_count", 1) or 1))
        stype = str(habit.get("schedule_type", "daily"))
        self.schedule_box.setCurrentText(stype)
        try:
            params = json.loads(habit.get("schedule_json") or "{}")
        except (json.JSONDecodeError, TypeError):
            params = {}
        if stype == "weekly_days":
            self.detail_edit.setText(",".join(str(d) for d in params.get("days", [])))
        elif stype == "interval":
            self.detail_edit.setText(str(params.get("every_n_days", 1)))
        elif stype in ("times_per_week", "times_per_month"):
            self.detail_edit.setText(str(params.get("times", 3)))
        else:
            self.detail_edit.setText("")

    def values(self) -> dict:
        """Validated dialog values -> store.create_habit kwargs."""
        name = self.name_edit.text().strip()
        if not name:
            raise ValueError("habit name is required")
        habit_type = self.type_box.currentText()
        schedule_type = self.schedule_box.currentText()
        detail = self.detail_edit.text().strip()
        schedule_json = "{}"
        if schedule_type == "weekly_days":
            days = [int(x) for x in detail.split(",") if x.strip().isdigit()]
            if not days:
                raise ValueError("weekly needs days like 1,3,5")
            schedule_json = json.dumps({"days": days})
        elif schedule_type == "interval":
            schedule_json = json.dumps({"every_n_days": int(detail or 1)})
        elif schedule_type in ("times_per_week", "times_per_month"):
            schedule_json = json.dumps({"times": int(detail or 3)})
        return {
            "name": name,
            "habit_type": habit_type,
            "target_count": int(self.target_spin.value()),
            "schedule_type": schedule_type,
            "schedule_json": schedule_json,
            "start_date": date.today().isoformat(),
        }
