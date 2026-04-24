"""Migration 006 — compliance audit + selective-delete tombstones (T12.36).

Adds the ``compliance_audit`` table and per-row tombstone columns
(``deleted_at``, ``deleted_reason``) on the sensitive tables that carry
category-partitioned PII:

* ``record_profiles`` — criminal record detail
* ``resume_versions`` — resume + cover-letter content
* ``engagement_events`` — email engagement history

S12a's ``ON DELETE CASCADE`` already handles session-level (whole-account)
deletion; tombstones are required only for category-level selective delete
where a worker wants to keep the account but purge one facet.

Schema notes
------------
* ``compliance_audit.session_id_hash`` is ``sha256(session_id)`` — we
  never store the raw session id on the audit row because audit rows
  outlive the session (they are the record of the deletion itself).
* ``actor_token_hash`` hashes whatever identifier the caller presents
  (worker feedback token or admin key) — matches the ``feature_flag_audit``
  convention from m002 for cross-table consistency.
* ``action`` is an open-vocabulary string; today we emit ``full_delete``,
  ``selective_delete``, ``export_requested``, ``export_downloaded``,
  ``retention_purge``. The table does not enforce the enum so new action
  labels can land without a migration.

Idempotency
-----------
The ``compliance_audit`` CREATE is ``IF NOT EXISTS``. Tombstone columns are
added via a PRAGMA pre-check so re-running the migration on a partially
applied DB is safe (SQLite lacks ``ADD COLUMN IF NOT EXISTS``).

Downgrade
---------
Drops the ``compliance_audit`` table and the three tombstone columns
(SQLite 3.35+ supports ``DROP COLUMN`` directly; Python 3.12 ships
3.40+). No data preservation on downgrade — this is a pure schema
round-trip.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 6

_AUDIT_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS compliance_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id_hash TEXT NOT NULL,
    action TEXT NOT NULL,
    category TEXT,
    actor_token_hash TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL
)
"""

_AUDIT_INDEXES: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_compliance_audit_action "
    "ON compliance_audit(action)",
    "CREATE INDEX IF NOT EXISTS idx_compliance_audit_session_hash "
    "ON compliance_audit(session_id_hash)",
    "CREATE INDEX IF NOT EXISTS idx_compliance_audit_created_at "
    "ON compliance_audit(created_at)",
)

# (table, column) pairs for tombstone additions.
_TOMBSTONE_TABLES: tuple[str, ...] = (
    "record_profiles",
    "resume_versions",
    "engagement_events",
)


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _add_tombstone_columns(conn: sqlite3.Connection, table: str) -> None:
    """Add deleted_at + deleted_reason to ``table`` (idempotent)."""
    if not _has_column(conn, table, "deleted_at"):
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN deleted_at TEXT"
        )
    if not _has_column(conn, table, "deleted_reason"):
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN deleted_reason TEXT"
        )


def _drop_tombstone_columns(conn: sqlite3.Connection, table: str) -> None:
    """Drop deleted_at + deleted_reason from ``table`` (no-op if absent)."""
    if _has_column(conn, table, "deleted_reason"):
        conn.execute(f"ALTER TABLE {table} DROP COLUMN deleted_reason")
    if _has_column(conn, table, "deleted_at"):
        conn.execute(f"ALTER TABLE {table} DROP COLUMN deleted_at")


def upgrade(conn: sqlite3.Connection) -> None:
    """Create compliance_audit + add tombstone columns (idempotent)."""
    conn.execute(_AUDIT_TABLE_DDL)
    for idx in _AUDIT_INDEXES:
        conn.execute(idx)
    for table in _TOMBSTONE_TABLES:
        _add_tombstone_columns(conn, table)


def downgrade(conn: sqlite3.Connection) -> None:
    """Drop compliance_audit + tombstone columns. Clean round-trip."""
    for table in _TOMBSTONE_TABLES:
        _drop_tombstone_columns(conn, table)
    conn.execute("DROP TABLE IF EXISTS compliance_audit")
