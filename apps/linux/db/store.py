"""SQLite store — S03: full SPEC §1 schema (5 tables)."""

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
