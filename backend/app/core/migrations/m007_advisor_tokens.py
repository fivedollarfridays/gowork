"""Migration 007 — advisor_tokens for case-manager advisor inbox (T12.31).

Adds the ``advisor_tokens`` table, the server-side row that backs
:func:`app.core.advisor_auth.require_advisor_token`. Every row carries
exactly one ``advisor_id`` and one ``city`` — the unit of
authorisation is the token, not the human (see
``docs/security/advisor-auth.md`` sections 2 + 14).

Schema notes
------------
* ``token_hash`` is ``SHA256(plaintext)`` — the plaintext ``mw_adv_``
  token is never persisted. Constant-time comparison is performed
  against this column.
* ``advisor_id`` is an opaque operator-assigned id (e.g.
  ``adv-jane-mtg``); it is SHA256-hashed before any audit-row write
  (see :mod:`app.core.advisor_auth`).
* ``city`` IS the claim — matches
  ``outcomes_records.payload_json.city`` until a future migration
  adds ``sessions.city``.
* ``revoked_at`` is the instant-revocation lever. Non-NULL rows are
  excluded from the partial active-token index below.
* ``expires_at`` is optional hard expiry. NULL = rotation-only, no
  time-based expiry.

Indexes
-------
Two indexes serve the hot path — ``SELECT ... WHERE token_hash = ?``
on every authenticated request, and ``UPDATE ... WHERE advisor_id = ?``
on revocation. The partial active-token index keeps the hot lookup
small by excluding revoked rows (revoked rows stay in the table for
audit per Section 8 of the runbook).

Idempotency
-----------
``CREATE TABLE IF NOT EXISTS`` and ``CREATE INDEX IF NOT EXISTS``
make upgrade safely re-runnable on partially-applied DBs.

Downgrade
---------
Drops the indexes then the table. Clean round-trip.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 7

_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS advisor_tokens (
    token_hash  TEXT PRIMARY KEY,
    advisor_id  TEXT NOT NULL,
    city        TEXT NOT NULL,
    issued_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at  TIMESTAMP,
    expires_at  TIMESTAMP
)
"""

_INDEXES: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_advisor_tokens_advisor_id "
    "ON advisor_tokens(advisor_id)",
    "CREATE INDEX IF NOT EXISTS idx_advisor_tokens_active "
    "ON advisor_tokens(advisor_id, city) WHERE revoked_at IS NULL",
)


def upgrade(conn: sqlite3.Connection) -> None:
    """Create advisor_tokens + supporting indexes (idempotent)."""
    conn.execute(_TABLE_DDL)
    for ddl in _INDEXES:
        conn.execute(ddl)


def downgrade(conn: sqlite3.Connection) -> None:
    """Drop advisor_tokens + its indexes. Clean round-trip."""
    conn.execute("DROP INDEX IF EXISTS idx_advisor_tokens_active")
    conn.execute("DROP INDEX IF EXISTS idx_advisor_tokens_advisor_id")
    conn.execute("DROP TABLE IF EXISTS advisor_tokens")
