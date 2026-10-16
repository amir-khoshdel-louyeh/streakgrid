"""Achievements — S06-2: 8 frozen codes (SPEC §5). Pure check + SQLite persist."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

ACHIEVEMENTS: dict[str, str] = {
    "first_step": "First Step",
    "week_warrior": "Week Warrior",
    "triplet": "Triplet",
    "perfect_day": "Perfect Day",
    "month_master": "Month Master",
    "day66": "66 Days",
    "half_century": "Half Century",
    "century_club": "Century Club",
}


def check_unlocks(
    total_completions: int = 0,
    best_current_streak: int = 0,
    habits_done_last_7d: int = 0,
    has_perfect_day: bool = False,
) -> list[str]:
    """Return newly-earned codes per SPEC §5 (pure, no DB)."""
    out: list[str] = []
    if total_completions >= 1:
        out.append("first_step")
    if best_current_streak >= 7:
        out.append("week_warrior")
    if habits_done_last_7d >= 3:
        out.append("triplet")
    if has_perfect_day:
        out.append("perfect_day")
    if best_current_streak >= 30:
        out.append("month_master")
    if best_current_streak >= 50:
        out.append("half_century")
    if best_current_streak >= 66:
        out.append("day66")
    if best_current_streak >= 100:
        out.append("century_club")
    return out


def unlock(conn: sqlite3.Connection, code: str) -> bool:
    """Insert achievement row if new. Returns True if freshly unlocked."""
    if code not in ACHIEVEMENTS:
        raise ValueError(f"unknown achievement: {code!r}")
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT OR IGNORE INTO achievements(code, name, unlocked_at) VALUES(?,?,?)",
        (code, ACHIEVEMENTS[code], now),
    )
    conn.commit()
    return cur.rowcount == 1


def is_unlocked(conn: sqlite3.Connection, code: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM achievements WHERE code=? AND unlocked_at IS NOT NULL", (code,)
    ).fetchone()
    return row is not None
