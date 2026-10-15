"""Streaks — S05-1: done predicate + pause helper (SPEC §3). Pure logic, no Qt."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping, Sequence, Union

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


def is_done(habit: Mapping[str, Any], value: int | None, has_row: bool) -> bool:
    """SPEC §3 done predicate.

    - yes_no: value >= 1
    - counter: value >= target_count
    - dont_do: done iff NO row (clean day); any row = slip = fail.
    """
    htype = _habit_get(habit, "type", "yes_no")
    if htype == "dont_do":
        return not has_row
    if not has_row or value is None:
        return False
    if htype == "counter":
        target = int(_habit_get(habit, "target_count", 1) or 1)
        return int(value) >= target
    return int(value) >= 1


def _pause_range(p: Any) -> tuple[date, date]:
    if isinstance(p, (list, tuple)) and len(p) >= 2:
        return _to_date(p[0]), _to_date(p[1])
    if isinstance(p, Mapping):
        return _to_date(p["start_date"]), _to_date(p["end_date"])
    return _to_date(getattr(p, "start_date")), _to_date(getattr(p, "end_date"))


def is_paused(pauses: Sequence[Any], on: DateLike) -> bool:
    """True if date `on` falls inside any pause range (inclusive)."""
    d = _to_date(on)
    for p in pauses or []:
        s, e = _pause_range(p)
        if s <= d <= e:
            return True
    return False
