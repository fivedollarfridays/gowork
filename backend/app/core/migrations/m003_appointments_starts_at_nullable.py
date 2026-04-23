"""Migration 003 — relax appointments.starts_at to allow NULL (T12.9).

Pathway-auto placeholders created by the barrier linker have no concrete
starts_at until the worker fills them in. The T12.6 Pydantic model
already treats `starts_at=None` as valid for `source="pathway_auto"`
records, but m002's NOT NULL constraint blocked persistence.

SQLite cannot drop NOT NULL in place, so we rebuild the table via the
standard create-new / copy / drop-old / rename pattern. Indexes are
re-created on the new table.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 3


_CREATE_NEW_TABLE = """
CREATE TABLE IF NOT EXISTS appointments_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    starts_at TEXT,
    ends_at TEXT,
    location_name TEXT,
    location_address TEXT,
    barrier_link TEXT,
    status TEXT NOT NULL DEFAULT 'scheduled',
    source TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
)
"""

_COPY_SQL = (
    "INSERT INTO appointments_new "
    "(id, session_id, type, title, starts_at, ends_at, location_name, "
    "location_address, barrier_link, status, source, notes, created_at) "
    "SELECT id, session_id, type, title, starts_at, ends_at, location_name, "
    "location_address, barrier_link, status, source, notes, created_at "
    "FROM appointments"
)

_INDEX_DDL: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_appointments_session_id ON appointments(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_appointments_starts_at ON appointments(starts_at)",
    "CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)",
)


def upgrade(conn: sqlite3.Connection) -> None:
    """Rebuild appointments table with nullable starts_at."""
    if not _table_exists(conn, "appointments"):
        return
    conn.execute(_CREATE_NEW_TABLE)
    conn.execute(_COPY_SQL)
    conn.execute("DROP TABLE appointments")
    conn.execute("ALTER TABLE appointments_new RENAME TO appointments")
    for ddl in _INDEX_DDL:
        conn.execute(ddl)


def downgrade(conn: sqlite3.Connection) -> None:
    """No-op — re-tightening NOT NULL would fail on existing placeholders."""
    return


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None
