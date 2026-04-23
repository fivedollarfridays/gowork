"""Migration 004 — single-use manage-appointment token replay protection (T12.10b).

Creates `used_tokens(token_hash TEXT PRIMARY KEY, used_at TEXT NOT NULL,
action TEXT NOT NULL, appointment_id INTEGER NOT NULL)`. The uniqueness of
`token_hash` combined with `INSERT OR IGNORE` is the atomic replay guard:
a double-click on an email CTA can only succeed once — the second INSERT
yields rowcount=0 and the verify path raises `TokenAlreadyUsed`.

We store `sha256(token)` rather than the token itself so that a DB dump
does not leak usable credentials. `action` + `appointment_id` are retained
for audit / forensics only; they do not participate in uniqueness.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 4


DDL_SQL = """
CREATE TABLE IF NOT EXISTS used_tokens (
    token_hash TEXT PRIMARY KEY,
    used_at TEXT NOT NULL,
    action TEXT NOT NULL,
    appointment_id INTEGER NOT NULL
)
"""

_INDEX_DDL: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_used_tokens_appointment_id "
    "ON used_tokens(appointment_id)",
)


def upgrade(conn: sqlite3.Connection) -> None:
    """Create the used_tokens table plus its audit index."""
    conn.execute(DDL_SQL)
    for ddl in _INDEX_DDL:
        conn.execute(ddl)


def downgrade(conn: sqlite3.Connection) -> None:
    """Drop the used_tokens table (downgrade clears all replay history)."""
    conn.execute("DROP TABLE IF EXISTS used_tokens")
