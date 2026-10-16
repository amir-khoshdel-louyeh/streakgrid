"""Streaks — S05-3: best + rate (SPEC §3). Pure logic, no Qt."""

from __future__ import annotations

from datetime import date, timedelta
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


def current_streak(
    habit: Mapping[str, Any],
    completions: Mapping[str, int],
    pauses: Sequence[Any] | None = None,
    today: DateLike | None = None,
) -> int:
    """Backwards walk from today (SPEC §3). Unscheduled + paused are skipped."""
    from .schedule import is_due

    pauses = pauses or []
    end = _to_date(today) if today is not None else date.today()
    start_raw = _habit_get(habit, "start_date")
    start = _to_date(start_raw) if start_raw else end - timedelta(days=365 * 3)
    if int(_habit_get(habit, "archived", 0) or 0) == 1:
        return 0

    streak = 0
    d = end
    while d >= start:
        iso = d.isoformat()
        if not is_due(habit, d):
            d -= timedelta(days=1)
            continue
        if is_paused(pauses, d):
            d -= timedelta(days=1)
            continue
        has_row = iso in completions
        done = is_done(habit, completions.get(iso), has_row)
        if done:
            streak += 1
        else:
            if d == end:
                # Today not yet done -> streak still alive, look back.
                d -= timedelta(days=1)
                continue
            break
        d -= timedelta(days=1)
    return streak


def best_streak(
    habit: Mapping[str, Any],
    completions: Mapping[str, int],
    pauses: Sequence[Any] | None = None,
    today: DateLike | None = None,
) -> int:
    """Max run over full history (SPEC §3)."""
    from .schedule import is_due

    pauses = pauses or []
    end = _to_date(today) if today is not None else date.today()
    start_raw = _habit_get(habit, "start_date")
    start = _to_date(start_raw) if start_raw else end - timedelta(days=365 * 3)
    if int(_habit_get(habit, "archived", 0) or 0) == 1:
        return 0

    best = run = 0
    d = start
    while d <= end:
        if not is_due(habit, d) or is_paused(pauses, d):
            d += timedelta(days=1)
            continue
        iso = d.isoformat()
        if is_done(habit, completions.get(iso), iso in completions):
            run += 1
            best = max(best, run)
        else:
            run = 0
        d += timedelta(days=1)
    return best


def completion_rate(
    habit: Mapping[str, Any],
    completions: Mapping[str, int],
    pauses: Sequence[Any] | None = None,
    today: DateLike | None = None,
    days: int = 30,
) -> float:
    """done_due / total_due over rolling window, paused excluded (SPEC §3)."""
    from .schedule import is_due

    pauses = pauses or []
    end = _to_date(today) if today is not None else date.today()
    start = end - timedelta(days=days - 1)
    habit_start_raw = _habit_get(habit, "start_date")
    habit_start = _to_date(habit_start_raw) if habit_start_raw else start
    done = total = 0
    d = max(start, habit_start)
    while d <= end:
        if is_due(habit, d) and not is_paused(pauses, d):
            total += 1
            iso = d.isoformat()
            if is_done(habit, completions.get(iso), iso in completions):
                done += 1
        d += timedelta(days=1)
    return (done / total) if total else 0.0
