"""SQLite store — S03: init + folders (SPEC §1)."""

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


def _connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.execute(_FOLDERS_DDL)
    conn.commit()


def init_db(path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = _connect(path)
    migrate(conn)
    return conn
