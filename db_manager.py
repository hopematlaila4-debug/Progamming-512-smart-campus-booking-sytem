"""
db_manager.py
-------------
All SQLite access goes through DatabaseManager. It creates the tables on
first run, runs parameterised queries (protects against SQL injection) and
seeds starter data so the system is usable immediately.

Tables
    campuses   - campus details + the key of its booking policy
    users      - accounts and roles (passwords stored as salted hashes)
    resources  - bookable resources, each linked to one campus
    bookings   - booking records linked to a resource, lecturer and campus
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS campuses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,
    policy_key  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    full_name     TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    role          TEXT NOT NULL
                  CHECK (role IN ('Lecturer', 'Campus Administrator', 'System Operator')),
    campus_id     INTEGER REFERENCES campuses(id),
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resources (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name          TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    capacity      INTEGER NOT NULL CHECK (capacity > 0),
    campus_id     INTEGER NOT NULL REFERENCES campuses(id),
    status        TEXT NOT NULL DEFAULT 'Active'
                  CHECK (status IN ('Active', 'Maintenance', 'Removed')),
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id      INTEGER NOT NULL REFERENCES resources(id),
    lecturer_id      INTEGER NOT NULL REFERENCES users(id),
    campus_id        INTEGER NOT NULL REFERENCES campuses(id),
    booking_date     TEXT NOT NULL,
    start_minutes    INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    purpose          TEXT NOT NULL DEFAULT '',
    status           TEXT NOT NULL DEFAULT 'Active'
                     CHECK (status IN ('Active', 'Cancelled')),
    created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bookings_resource_date ON bookings (resource_id, booking_date);
CREATE INDEX IF NOT EXISTS idx_bookings_lecturer      ON bookings (lecturer_id);
CREATE INDEX IF NOT EXISTS idx_bookings_campus        ON bookings (campus_id);
"""


class DatabaseManager:
    """Thin wrapper around a single SQLite connection."""

    def __init__(self, db_path: str | Path = config.DB_PATH, seed: bool = True):
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row          # rows behave like dictionaries
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        if seed:
            from database.seed_data import seed_database   # imported here to avoid a circular import
            seed_database(self)

    # ----------------------------------------------------------------- helpers
    @contextmanager
    def transaction(self):
        """Commit on success, roll back if anything inside the block fails."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Run a SELECT and return every row."""
        return self.conn.execute(sql, params).fetchall()

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        """Run a SELECT and return the first row (or None)."""
        return self.conn.execute(sql, params).fetchone()

    def execute(self, sql: str, params: tuple = ()) -> int:
        """Run INSERT / UPDATE / DELETE, commit, and return the last inserted id."""
        with self.transaction():
            cursor = self.conn.execute(sql, params)
        return cursor.lastrowid

    def close(self) -> None:
        self.conn.close()
