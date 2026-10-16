"""Heatmap — S06-1: 53x7 intensity matrix (SPEC §4). Pure logic, no Qt."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Mapping, Union

DateLike = Union[date, str]


def _to_date(d: DateLike) -> date:
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def intensity(value: int | None, target: int = 1) -> int:
    """0-4 level from value/target (SPEC §4). None/0 -> 0."""
    if not value:
        return 0
    t = max(1, int(target or 1))
    ratio = float(value) / t
    if ratio < 0.33:
        return 1
    if ratio < 0.66:
        return 2
    if ratio < 1.0:
        return 3
    return 4


def build_matrix(
    completions: Mapping[str, int],
    end_date: DateLike | None = None,
    days: int = 365,
    target: int = 1,
) -> list[list[int]]:
    """Return 53 cols x 7 rows (Mon=0). Oldest week left, current week right."""
    end = _to_date(end_date) if end_date is not None else date.today()
    grid: list[list[int]] = [[0] * 7 for _ in range(53)]
    end_monday = end - timedelta(days=end.weekday())
    for iso, val in (completions or {}).items():
        try:
            d = _to_date(iso)
        except ValueError:
            continue
        delta = (end - d).days
        if delta < 0 or delta >= days:
            continue
        monday = d - timedelta(days=d.weekday())
        col = 52 - ((end_monday - monday).days // 7)
        if 0 <= col < 53:
            grid[col][d.weekday()] = max(grid[col][d.weekday()], intensity(val, target))
    return grid
