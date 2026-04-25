"""Retention sweep — purges sessions past ``expires_at + 90d`` (T12.36).

Runs as a nightly step (:mod:`scripts.nightly_digest`). For every
session where ``expires_at`` is older than ``now - 90d``, issues the
same ``DELETE FROM sessions`` that :mod:`delete` uses (FK CASCADE clears
every child row) and writes one ``compliance_audit`` row per purge.

Purge is all-or-nothing for each session: the CASCADE chain is atomic
inside a single connection. Errors on a single session are logged but
never abort the loop (matches the T12.24/T12.25a robustness contract
for nightly steps).
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.modules.compliance._audit import write_audit
from app.modules.compliance.delete import _NON_CASCADING_TABLES

__all__ = ["RETENTION_GRACE_DAYS", "retention_sweep"]

logger = logging.getLogger(__name__)

RETENTION_GRACE_DAYS = 90


def retention_sweep(
    *, db_path: str | Path, now: datetime | None = None,
) -> list[str]:
    """Purge sessions past ``expires_at + RETENTION_GRACE_DAYS``.

    Returns the list of purged ``session_id`` values. Writes one audit
    row per purge. Does not fail if individual purges hit errors —
    the row is skipped and logged.
    """
    resolved_now = now if now is not None else datetime.now(timezone.utc)
    cutoff_iso = (
        resolved_now - timedelta(days=RETENTION_GRACE_DAYS)
    ).isoformat()
    candidates = _select_stale_sessions(db_path, cutoff_iso)
    purged: list[str] = []
    for session_id in candidates:
        if _purge_one(session_id, db_path, resolved_now):
            purged.append(session_id)
    return purged


def _select_stale_sessions(
    db_path: str | Path, cutoff_iso: str,
) -> list[str]:
    """Return ids whose ``expires_at`` is ``<=`` ``cutoff_iso`` (ISO compare)."""
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id FROM sessions WHERE expires_at <= ?",
            (cutoff_iso,),
        ).fetchall()
    finally:
        conn.close()
    return [str(row[0]) for row in rows]


def _purge_one(
    session_id: str, db_path: str | Path, now: datetime,
) -> bool:
    """Delete one session + cascade; audit. Returns True on success.

    Mirrors the cascade contract of :func:`compliance.delete.full_delete`:
    the m002+ session-scoped tables ride the SQLite FK cascade triggered
    by the parent DELETE, but the m001 ``session_id``-but-no-FK tables
    (``record_profiles``, ``feedback_tokens``, ``visit_feedback``,
    ``resource_feedback``, ``share_tokens``) MUST be cleared explicitly
    or the sweep leaks orphaned PII rows. Same ``_NON_CASCADING_TABLES``
    list, same explicit-DELETE-before-parent-DELETE order.
    """
    try:
        write_audit(
            db_path=db_path, session_id=session_id,
            action="retention_purge",
            payload={"retention_grace_days": RETENTION_GRACE_DAYS},
            now=now,
        )
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            for table in _NON_CASCADING_TABLES:
                conn.execute(
                    f"DELETE FROM {table} WHERE session_id = ?",
                    (session_id,),
                )
            conn.execute(
                "DELETE FROM sessions WHERE id = ?", (session_id,),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 — never abort the sweep batch
        logger.exception(
            "retention purge failed for session_id=%s; skipping", session_id,
        )
        return False
    return True
