"""SQL fragments + row (de)serialisation helpers for OutcomeTracker.

Extracted from tracker.py to keep the public module under the 15-function
architecture limit. Purely stateless — no DB connections held here.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.modules.outcomes.types import BarrierOutcome, OutcomeRecord


INSERT_SQL = (
    "INSERT INTO outcomes_records "
    "(session_id, event_type, payload_json, created_at, "
    "barriers_cleared_snapshot_json) "
    "VALUES (?, ?, ?, ?, ?)"
)

SELECT_BY_SESSION_SQL = (
    "SELECT session_id, event_type, payload_json, created_at, "
    "barriers_cleared_snapshot_json "
    "FROM outcomes_records "
    "WHERE session_id = ? "
    "ORDER BY created_at ASC, id ASC"
)

SELECT_ALL_SQL = (
    "SELECT session_id, event_type, payload_json, created_at, "
    "barriers_cleared_snapshot_json "
    "FROM outcomes_records ORDER BY created_at ASC, id ASC"
)

_SELECT_BY_CITY_BASE = (
    "SELECT session_id, event_type, payload_json, created_at, "
    "barriers_cleared_snapshot_json "
    "FROM outcomes_records WHERE 1=1"
)


def now_iso() -> str:
    """Return UTC now as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with foreign_keys enforced."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def serialize_payload(record: OutcomeRecord) -> str:
    """Serialize the non-snapshot payload fields to JSON for storage."""
    payload = {
        "plan_accuracy": record.plan_accuracy,
        "resource_ratings": record.resource_ratings,
        "city": record.city,
    }
    return json.dumps(payload)


def serialize_snapshot(record: OutcomeRecord) -> str:
    """Serialize barrier_outcomes list for the snapshot column."""
    return json.dumps([bo.model_dump() for bo in record.barrier_outcomes])


def row_to_record(row: tuple) -> OutcomeRecord:
    """Hydrate a DB row into an OutcomeRecord Pydantic model."""
    session_id, event_type, payload_json, created_at, snapshot_json = row
    payload = _parse_payload(payload_json)
    return OutcomeRecord(
        session_id=session_id,
        signal_type=event_type,
        barrier_outcomes=_parse_snapshot(snapshot_json),
        plan_accuracy=payload.get("plan_accuracy"),
        resource_ratings=payload.get("resource_ratings") or {},
        city=payload.get("city") or "",
        created_at=created_at,
    )


def build_list_recent_sql(
    event_type: str | None,
    since: datetime | None,
) -> tuple[str, list[Any]]:
    """Compose the WHERE clause + params for list_recent filters."""
    sql = _SELECT_BY_CITY_BASE + " AND json_extract(payload_json, '$.city') = ?"
    params: list[Any] = []
    if event_type is not None:
        sql += " AND event_type = ?"
        params.append(event_type)
    if since is not None:
        sql += " AND created_at >= ?"
        params.append(since.isoformat())
    sql += " ORDER BY created_at ASC, id ASC"
    return sql, params


# -------- Private helpers --------


def _parse_payload(raw: str | None) -> dict[str, Any]:
    """Parse the JSON payload column, returning an empty dict on failure."""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _parse_snapshot(raw: str | None) -> list[BarrierOutcome]:
    """Parse the snapshot column back into BarrierOutcome objects."""
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    return [BarrierOutcome(**item) for item in data if isinstance(item, dict)]
