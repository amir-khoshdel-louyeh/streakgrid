"""Scheduling — S04-3: is_due + next_due (SPEC §2). Pure logic, no Qt."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Mapping, Union

DateLike = Union[date, str]


def _to_date(d: DateLike) -> date:
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def _habit_get(habit: Mapping[str, Any], key: str, default: Any = None) -> Any:
    try:
        return habit[key]
    except (KeyError, TypeError, IndexError):
        return getattr(habit, key, default)


def _schedule_json(habit: Mapping[str, Any]) -> dict:
    raw = _habit_get(habit, "schedule_json", "{}") or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def is_due(habit: Mapping[str, Any], on: DateLike) -> bool:
    """Return True if habit is scheduled on date `on` (SPEC §2)."""
    d = _to_date(on)
    if int(_habit_get(habit, "archived", 0) or 0) == 1:
        return False
    start_raw = _habit_get(habit, "start_date")
    if start_raw:
        if d < _to_date(start_raw):
            return False
    stype = _habit_get(habit, "schedule_type", "daily")
    if stype == "daily":
        return True
    if stype == "weekly_days":
        days = _schedule_json(habit).get("days", [])
        return d.isoweekday() in set(days)
    if stype == "interval":
        n = int(_schedule_json(habit).get("every_n_days", 1) or 1)
        if n <= 0:
            raise ValueError("every_n_days must be >= 1")
        start = _to_date(_habit_get(habit, "start_date"))
        return (d - start).days % n == 0
    if stype in ("times_per_week", "times_per_month"):
        # Flexible goal: every day counts as due (SPEC §2).
        return True
    raise ValueError(f"unsupported schedule_type: {stype!r}")


def is_due_today(habit: Mapping[str, Any], today: DateLike | None = None) -> bool:
    from datetime import date as _d

    return is_due(habit, today or _d.today())


def next_due(habit: Mapping[str, Any], from_date: DateLike | None = None) -> date | None:
    """Next due date on/after `from_date` (None if archived/never)."""
    from datetime import timedelta, date as _d

    start = _to_date(from_date or _d.today())
    for i in range(0, 400):
        cand = start + timedelta(days=i)
        if is_due(habit, cand):
            return cand
    return None
