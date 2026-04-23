"""DB-backed append-only OutcomeTracker.

Records outcome signals in the `outcomes_records` table created by
migration m002. Every `record_outcome()` call is an INSERT — never an
upsert — so full per-session history is preserved across runs and
nightly jobs. This is the WRITE side of the N+1 intelligence loop.

Reference patterns:
- ops:lib/conversion_tracking.log_conversion (append-only inserts)
- ops:lib/block_decisions.record_decision (append-only inserts)

Thread-safe for single-process use (SQLite + GIL). Each public method
opens a short-lived connection so concurrent processes don't trip over
a shared handle.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.modules.outcomes.tracker_sql import (
    INSERT_SQL,
    SELECT_ALL_SQL,
    SELECT_BY_SESSION_SQL,
    build_list_recent_sql,
    connect,
    now_iso,
    row_to_record,
    serialize_payload,
    serialize_snapshot,
)
from app.modules.outcomes.types import OutcomeRecord


class OutcomeTracker:
    """Append-only outcome store backed by SQLite.

    All writes go straight to `outcomes_records`; all reads hit the DB.
    There is no in-process cache — per-process restart durability falls
    out of that guarantee for free.
    """

    def __init__(self, db_path: str | Path) -> None:
        """Bind to the SQLite file at `db_path`.

        The file must already have migration m002 applied so that the
        `outcomes_records` table exists. Callers typically pass the
        path returned by `app.core.migrations.runner.apply_pending`.
        """
        self._db_path = str(db_path)

    # ---- Writes ----

    def record_outcome(self, record: OutcomeRecord) -> None:
        """Append an outcome record (INSERT — never upsert).

        If `record.created_at` is unset, fills in the current UTC time
        as an ISO-8601 string before persisting.
        """
        created_at = record.created_at or now_iso()
        conn = connect(self._db_path)
        try:
            conn.execute(
                INSERT_SQL,
                (
                    record.session_id,
                    record.signal_type,
                    serialize_payload(record),
                    created_at,
                    serialize_snapshot(record),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    # ---- Reads ----

    def list_by_session(self, session_id: str) -> list[OutcomeRecord]:
        """Return all records for a session, ordered chronologically (oldest first)."""
        conn = connect(self._db_path)
        try:
            rows = conn.execute(SELECT_BY_SESSION_SQL, (session_id,)).fetchall()
        finally:
            conn.close()
        return [row_to_record(r) for r in rows]

    def list_recent(
        self,
        city: str,
        event_type: str | None = None,
        since: datetime | None = None,
    ) -> list[OutcomeRecord]:
        """Return records for a city, optionally filtered by event_type and since.

        Args:
            city: City slug (matches the `city` field stored in payload_json).
            event_type: Optional `event_type` filter (matches `signal_type`).
            since: Optional cutoff; only records with created_at >= since returned.

        Returns:
            Chronologically ordered list of matching records.
        """
        sql, params = build_list_recent_sql(event_type, since)
        conn = connect(self._db_path)
        try:
            rows = conn.execute(sql, [city, *params]).fetchall()
        finally:
            conn.close()
        return [row_to_record(r) for r in rows]

    def get_latest(self, session_id: str) -> OutcomeRecord | None:
        """Return the most recent record for a session, or None if none exist.

        Convenience wrapper over `list_by_session(session_id)[-1]`; preserved
        for backwards compatibility with callers that only care about the
        latest signal (e.g. the intelligence read path).
        """
        records = self.list_by_session(session_id)
        return records[-1] if records else None

    # ---- Legacy convenience reads (keep existing callers green) ----

    def count(self) -> int:
        """Total outcome records stored (across all sessions)."""
        conn = connect(self._db_path)
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM outcomes_records"
            ).fetchone()
        finally:
            conn.close()
        return int(row[0]) if row else 0

    def get_outcomes_for_city(self, city: str) -> list[OutcomeRecord]:
        """Retrieve all outcomes for a specific city (legacy aggregator API)."""
        return self.list_recent(city=city)

    def get_all_outcomes(self) -> list[OutcomeRecord]:
        """Retrieve every stored outcome, chronological. Legacy API."""
        conn = connect(self._db_path)
        try:
            rows = conn.execute(SELECT_ALL_SQL).fetchall()
        finally:
            conn.close()
        return [row_to_record(r) for r in rows]
