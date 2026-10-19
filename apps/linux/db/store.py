"""SQLite store — S20-2: CSV export helper."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = str(Path.home() / ".local" / "share" / "streakgrid" / "streakgrid.db")

_FOLDERS_DDL = """
CREATE TABLE IF NOT EXISTS folders(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  color TEXT NOT NULL DEFAULT '#888888',
  sort_order INTEGER NOT NULL DEFAULT 0
);
"""


_HABITS_DDL = """
CREATE TABLE IF NOT EXISTS habits(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('yes_no','counter','dont_do')),
  target_count INTEGER NOT NULL DEFAULT 1,
  schedule_type TEXT NOT NULL CHECK(schedule_type IN
    ('daily','weekly_days','interval','times_per_week','times_per_month')),
  schedule_json TEXT NOT NULL DEFAULT '{}',
  start_date TEXT NOT NULL,
  created_at TEXT NOT NULL,
  archived INTEGER NOT NULL DEFAULT 0
);
"""

_COMPLETIONS_DDL = """
CREATE TABLE IF NOT EXISTS completions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
  date TEXT NOT NULL,
  value INTEGER NOT NULL DEFAULT 1,
  note TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL,
  UNIQUE(habit_id, date)
);
CREATE INDEX IF NOT EXISTS idx_completions_habit_date
  ON completions(habit_id, date);
"""

_PAUSES_DDL = """
CREATE TABLE IF NOT EXISTS pauses(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  reason TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_pauses_habit_range
  ON pauses(habit_id, start_date, end_date);
"""

_ACHIEVEMENTS_DDL = """
CREATE TABLE IF NOT EXISTS achievements(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  unlocked_at TEXT
);
"""


def _connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.execute(_FOLDERS_DDL)
    conn.execute(_HABITS_DDL)
    conn.executescript(_COMPLETIONS_DDL)
    conn.executescript(_PAUSES_DDL)
    conn.execute(_ACHIEVEMENTS_DDL)
    conn.commit()


def init_db(path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = _connect(path)
    migrate(conn)
    return conn


def create_habit(
    conn: sqlite3.Connection,
    *,
    name: str,
    habit_type: str = "yes_no",
    target_count: int = 1,
    schedule_type: str = "daily",
    schedule_json: str = "{}",
    start_date: str,
    folder_id: int | None = None,
) -> int:
    """Insert habit, return row id. Minimal validation for S08 dialog."""
    from datetime import datetime, timezone

    name = (name or "").strip()
    if not name:
        raise ValueError("habit name is required")
    if habit_type not in ("yes_no", "counter", "dont_do"):
        raise ValueError(f"bad type: {habit_type!r}")
    if schedule_type not in (
        "daily",
        "weekly_days",
        "interval",
        "times_per_week",
        "times_per_month",
    ):
        raise ValueError(f"bad schedule: {schedule_type!r}")
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """INSERT INTO habits(name, folder_id, type, target_count, schedule_type,
                              schedule_json, start_date, created_at, archived)
           VALUES(?,?,?,?,?,?,?,?,0)""",
        (name, folder_id, habit_type, int(target_count or 1),
         schedule_type, schedule_json, start_date, now),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_habits(conn: sqlite3.Connection, *, include_archived: bool = False) -> list[sqlite3.Row]:
    if include_archived:
        return list(conn.execute("SELECT * FROM habits ORDER BY id"))
    return list(conn.execute("SELECT * FROM habits WHERE archived=0 ORDER BY id"))


def get_completions(conn: sqlite3.Connection, habit_id: int) -> dict[str, int]:
    rows = conn.execute(
        "SELECT date, value FROM completions WHERE habit_id=?", (habit_id,)
    ).fetchall()
    return {r["date"]: int(r["value"]) for r in rows}


def log_completion(
    conn: sqlite3.Connection,
    habit_id: int,
    on_date: str,
    value: int = 1,
    note: str = "",
) -> None:
    """Upsert today's completion (one-tap check-off for S09)."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO completions(habit_id, date, value, note, updated_at)
           VALUES(?,?,?,?,?)
           ON CONFLICT(habit_id, date) DO UPDATE SET value=excluded.value,
             note=excluded.note, updated_at=excluded.updated_at""",
        (habit_id, on_date, int(value), note, now),
    )
    conn.commit()


def get_completion(conn: sqlite3.Connection, habit_id: int, on_date: str) -> sqlite3.Row | None:
    """Single day row for retroactive editing (S11)."""
    return conn.execute(
        "SELECT * FROM completions WHERE habit_id=? AND date=?", (habit_id, on_date)
    ).fetchone()


def clear_completion(conn: sqlite3.Connection, habit_id: int, on_date: str) -> None:
    """Delete one day (untick in detail dialog)."""
    conn.execute(
        "DELETE FROM completions WHERE habit_id=? AND date=?", (habit_id, on_date)
    )
    conn.commit()


def create_folder(conn: sqlite3.Connection, name: str, color: str = "#888888") -> int:
    name = (name or "").strip()
    if not name:
        raise ValueError("folder name is required")
    order = conn.execute("SELECT COALESCE(MAX(sort_order), -1)+1 FROM folders").fetchone()[0]
    cur = conn.execute(
        "INSERT INTO folders(name, color, sort_order) VALUES(?,?,?)",
        (name, color, int(order)),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_folders(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM folders ORDER BY sort_order, id"))


def set_habit_folder(conn: sqlite3.Connection, habit_id: int, folder_id: int | None) -> None:
    conn.execute("UPDATE habits SET folder_id=? WHERE id=?", (folder_id, habit_id))
    conn.commit()


def add_pause(
    conn: sqlite3.Connection, habit_id: int, start_date: str, end_date: str, reason: str = ""
) -> int:
    if start_date > end_date:
        raise ValueError("pause start must be <= end")
    cur = conn.execute(
        "INSERT INTO pauses(habit_id, start_date, end_date, reason) VALUES(?,?,?,?)",
        (habit_id, start_date, end_date, reason),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_pauses(conn: sqlite3.Connection, habit_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM pauses WHERE habit_id=? ORDER BY start_date", (habit_id,)
        )
    )


def export_completions_csv(conn: sqlite3.Connection, out_path: str) -> str:
    """Export (habit, date, value, note) rows to CSV. Returns path."""
    import csv

    rows = conn.execute(
        """SELECT h.name AS habit, c.date AS date, c.value AS value,
                  c.note AS note, c.updated_at AS updated_at
           FROM completions c JOIN habits h ON h.id=c.habit_id
           ORDER BY h.name, c.date"""
    ).fetchall()
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["habit", "date", "value", "note", "updated_at"])
        for r in rows:
            writer.writerow([r["habit"], r["date"], r["value"], r["note"], r["updated_at"]])
    return out_path
