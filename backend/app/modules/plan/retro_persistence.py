"""SQLite persistence for daily retro snapshots (T12.22).

Split from ``daily_progress.py`` to keep each module under the 12-function
ceiling. Handles JSON (de)serialization for the three JSON columns on
``daily_progress_snapshots`` and enforces a single-row-per-(session, date)
upsert contract via explicit SELECT-then-UPDATE-or-INSERT (the migration
does not declare a UNIQUE constraint).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from app.modules.plan.evidence_collector import EvidenceBundle


def _serialize_actions(actions: list) -> str:
    """Dump a list of RetroAction models to JSON using pydantic."""
    return json.dumps([a.model_dump(mode="json") for a in actions])


def _deserialize_actions(payload: str | None) -> list[dict]:
    if not payload:
        return []
    return json.loads(payload)


def _existing_id(
    conn: sqlite3.Connection, session_id: str, for_date: str,
) -> int | None:
    row = conn.execute(
        "SELECT id FROM daily_progress_snapshots "
        "WHERE session_id = ? AND date = ?",
        (session_id, for_date),
    ).fetchone()
    return int(row[0]) if row else None


def _update_row(
    conn: sqlite3.Connection, row_id: int, payload: tuple[str, str, str, str],
) -> None:
    """UPDATE the three JSON columns + created_at stamp on an existing row."""
    conn.execute(
        "UPDATE daily_progress_snapshots SET "
        "expected_actions_json = ?, evidence_json = ?, "
        "classifications_json = ?, created_at = ? WHERE id = ?",
        (*payload, row_id),
    )


def _insert_row(
    conn: sqlite3.Connection,
    session_id: str,
    for_date_str: str,
    payload: tuple[str, str, str, str],
) -> None:
    """INSERT a fresh snapshot row."""
    conn.execute(
        "INSERT INTO daily_progress_snapshots "
        "(session_id, date, expected_actions_json, evidence_json, "
        "classifications_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, for_date_str, *payload),
    )


def upsert_snapshot(
    *,
    session_id: str,
    for_date: date,
    expected_actions: list[dict],
    evidence: EvidenceBundle,
    actions: list,
    db_path: str | Path,
) -> None:
    """Insert or update the snapshot row for (session_id, for_date)."""
    date_str = for_date.isoformat()
    payload = (
        json.dumps(expected_actions),
        evidence.model_dump_json(),
        _serialize_actions(actions),
        datetime.now(timezone.utc).isoformat(),
    )
    conn = sqlite3.connect(str(db_path))
    try:
        existing = _existing_id(conn, session_id, date_str)
        if existing is not None:
            _update_row(conn, existing, payload)
        else:
            _insert_row(conn, session_id, date_str, payload)
        conn.commit()
    finally:
        conn.close()


def fetch_snapshot(
    *, session_id: str, for_date: date, db_path: str | Path,
) -> dict | None:
    """Return the raw column values for the (session, date) snapshot or None."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT expected_actions_json, evidence_json, "
            "classifications_json FROM daily_progress_snapshots "
            "WHERE session_id = ? AND date = ?",
            (session_id, for_date.isoformat()),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {
        "expected_actions": _deserialize_actions(row[0]),
        "evidence_json": row[1],
        "classifications": _deserialize_actions(row[2]),
    }


__all__ = ["fetch_snapshot", "upsert_snapshot"]
