"""Worker data deletion — full cascade + selective tombstone (T12.36).

Two delete modes:

* :func:`full_delete` — ``DELETE FROM sessions WHERE id = ?`` with
  foreign keys enforced, triggering the ``ON DELETE CASCADE`` chain
  across every S12 table (m002). Records one ``compliance_audit`` row
  with action ``full_delete``.

* :func:`selective_delete` — soft-delete the specific rows associated
  with a category (currently ``criminal_record`` → ``record_profiles``).
  Sets ``deleted_at`` / ``deleted_reason`` (m006 columns). Reads must
  filter ``WHERE deleted_at IS NULL`` to respect the tombstone.

:func:`read_record_profile` exposes the canonical tombstone-aware
reader for ``record_profiles`` so route handlers (and other modules)
don't re-implement the filter. Extend with additional ``read_*``
helpers as more categories ship.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.modules.compliance._audit import write_audit

__all__ = [
    "CATEGORY_TO_TABLE",
    "full_delete",
    "selective_delete",
    "read_record_profile",
]


# Maps a public category label to the table whose rows carry that
# category's PII. The set is intentionally narrow — only categories for
# which a selective-delete lane is in scope.
CATEGORY_TO_TABLE: dict[str, str] = {
    "criminal_record": "record_profiles",
}


# --------------------------------------------------------------- full delete

# ``record_profiles`` predates the S12 CASCADE contract (m001 shipped
# it with a plain ``session_id TEXT UNIQUE`` — no FK). Full delete must
# clear it manually; every m002 child does fall off the CASCADE.
_NON_CASCADING_TABLES: tuple[str, ...] = ("record_profiles",)


def full_delete(
    session_id: str,
    *,
    db_path: str | Path,
    reason: str,
    actor_token: str | None,
    now: datetime | None = None,
) -> None:
    """Delete the session and cascade through every FK child (m002).

    Also clears ``record_profiles`` explicitly because m001 did not
    declare a FK on its ``session_id`` column (pre-dates S12a's CASCADE
    contract).
    """
    ts = now if now is not None else datetime.now(timezone.utc)
    # Audit FIRST — the cascading DELETE removes the row we are auditing,
    # but audit rows carry only a hashed id so they survive as an
    # independent record.
    write_audit(
        db_path=db_path, session_id=session_id,
        action="full_delete", actor_token=actor_token,
        payload={"reason": reason}, now=ts,
    )
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        for table in _NON_CASCADING_TABLES:
            conn.execute(
                f"DELETE FROM {table} WHERE session_id = ?", (session_id,),
            )
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------- selective delete

def selective_delete(
    session_id: str,
    *,
    category: str,
    db_path: str | Path,
    reason: str,
    actor_token: str | None,
    now: datetime | None = None,
) -> None:
    """Tombstone the rows tied to ``category`` for this session."""
    table = CATEGORY_TO_TABLE.get(category)
    if table is None:
        raise ValueError(f"unknown selective-delete category: {category!r}")
    ts = (now if now is not None else datetime.now(timezone.utc)).isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            f"UPDATE {table} SET deleted_at = ?, deleted_reason = ? "
            "WHERE session_id = ? AND deleted_at IS NULL",
            (ts, reason, session_id),
        )
        conn.commit()
    finally:
        conn.close()
    write_audit(
        db_path=db_path, session_id=session_id,
        action="selective_delete", category=category,
        actor_token=actor_token,
        payload={"reason": reason, "table": table},
        now=now,
    )


# --------------------------------------------------------------- tombstone-aware reads

def read_record_profile(
    session_id: str, *, db_path: str | Path,
) -> dict | None:
    """Return the live record_profiles row (or None if absent / tombstoned)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM record_profiles "
            "WHERE session_id = ? AND deleted_at IS NULL",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None
