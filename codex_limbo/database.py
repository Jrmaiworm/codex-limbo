"""SQLite store for numeric usage and quota snapshots only."""
import sqlite3
from pathlib import Path
from .config import data_dir


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or data_dir() / "usage.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS usage (
            session_id TEXT NOT NULL, timestamp TEXT NOT NULL, model TEXT NOT NULL,
            project TEXT NOT NULL, input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL, total_tokens INTEGER NOT NULL,
            PRIMARY KEY (session_id, timestamp)
        );
        CREATE INDEX IF NOT EXISTS usage_time ON usage(timestamp);
        CREATE TABLE IF NOT EXISTS quota (
            session_id TEXT NOT NULL, timestamp TEXT NOT NULL, limit_id TEXT NOT NULL,
            window_name TEXT NOT NULL, used_percent REAL NOT NULL,
            resets_at INTEGER, credits TEXT,
            PRIMARY KEY (session_id, timestamp, limit_id, window_name)
        );
        CREATE INDEX IF NOT EXISTS quota_time ON quota(timestamp);
    """)
    return db


def save(db: sqlite3.Connection, usage: list[tuple], quota: list[tuple]) -> None:
    with db:
        db.executemany("INSERT OR REPLACE INTO usage VALUES (?,?,?,?,?,?,?)", usage)
        db.executemany("INSERT OR REPLACE INTO quota VALUES (?,?,?,?,?,?,?)", quota)
