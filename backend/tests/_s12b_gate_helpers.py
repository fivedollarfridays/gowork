"""Shared helpers for the S12b integration gate test files (T12.35b).

Extracted from ``test_s12b_gate.py`` so that both the wiring/migration
gate file and the endpoint-auth gate file stay under the arch
600-line / 30-import / 50-line-per-function limits without
duplicating SQLite plumbing across the two modules.

Pure test utilities — no production logic, no fixtures (those live
on each test file directly).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.migrations import runner

__all__ = [
    "apply_all_migrations",
    "has_column",
    "list_tables",
    "schema_version",
    "seed_appointment_with_session",
]


def apply_all_migrations(db_path: str) -> None:
    """Apply every discovered migration via the production runner."""
    runner.apply_pending(db_path)


def list_tables(db_path: str) -> set[str]:
    """Return every user table name in the database."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    finally:
        conn.close()
    return {r[0] for r in rows}


def has_column(db_path: str, table: str, column: str) -> bool:
    """True if ``table`` has a column named ``column``."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    finally:
        conn.close()
    return any(row[1] == column for row in rows)


def schema_version(db_path: str) -> int:
    """Return MAX(version) from schema_migrations, 0 if absent."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()
    finally:
        conn.close()
    return int(rows[0]) if rows and rows[0] is not None else 0


def seed_appointment_with_session(
    db_path: str, *, appointment_id: int,
    session_id: str = "sess-rot-000",
) -> None:
    """Insert a sessions + appointments row pair for token-verify tests."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, '2026-04-23T00:00:00Z', '[]', "
            "'2026-05-23T00:00:00Z')",
            (session_id,),
        )
        conn.execute(
            "INSERT INTO appointments "
            "(id, session_id, type, title, starts_at, status, created_at) "
            "VALUES (?, ?, 'interview', 'T', '2026-04-23T00:00:00Z', "
            "'scheduled', '2026-04-23T00:00:00Z')",
            (appointment_id, session_id),
        )
        conn.commit()
    finally:
        conn.close()


# Silence unused-import warning — keep Path available for future helpers.
_ = Path
