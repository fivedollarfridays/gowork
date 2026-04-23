"""Tests for outcome tracker -- recording and storing outcome signals.

Updated for T12.0a: OutcomeTracker is now DB-backed and append-only.
Tests that previously relied on upsert semantics (replace) have been
updated to match the new insert-only behaviour — duplicates are no
longer replaced, they accumulate.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.migrations import runner
from app.modules.outcomes.tracker import OutcomeTracker
from app.modules.outcomes.types import BarrierOutcome, OutcomeRecord


def _prepare_db(tmp_path: Path) -> str:
    """Run migrations on a fresh temp DB and return its path."""
    db_path = str(tmp_path / "tracker.db")
    runner.apply_pending(db_path)
    return db_path


def _ensure_session(db_path: str, session_id: str) -> None:
    """Insert a parent sessions row so FK constraints are satisfied."""
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, now, "[]", now),
        )
        conn.commit()
    finally:
        conn.close()


def _record(tracker: OutcomeTracker, db_path: str, record: OutcomeRecord) -> None:
    """Seed session row then record outcome (convenience wrapper)."""
    _ensure_session(db_path, record.session_id)
    tracker.record_outcome(record)


class TestStoreOutcome:
    """Tracker must persist outcome records to the DB-backed store."""

    def test_store_single_outcome(self, tmp_path: Path) -> None:
        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        record = OutcomeRecord(
            session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            barrier_outcomes=[
                BarrierOutcome(barrier_id="criminal_record", resolved=True, weeks_to_resolve=8),
            ],
            city="fort-worth",
        )
        _record(tracker, db_path, record)
        assert tracker.count() == 1

    def test_store_multiple_outcomes(self, tmp_path: Path) -> None:
        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        for i in range(5):
            sid = f"aaaa{i:04d}-bbbb-cccc-dddd-eeeeeeeeeeee"
            record = OutcomeRecord(
                session_id=sid,
                signal_type="barrier_resolved",
                barrier_outcomes=[
                    BarrierOutcome(barrier_id="credit", resolved=True, weeks_to_resolve=4),
                ],
                city="fort-worth",
            )
            _record(tracker, db_path, record)
        assert tracker.count() == 5

    def test_duplicate_session_appends_not_replaces(self, tmp_path: Path) -> None:
        """Append-only: a second outcome for the same session accumulates."""
        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        record1 = OutcomeRecord(
            session_id=sid,
            signal_type="barrier_resolved",
            barrier_outcomes=[
                BarrierOutcome(barrier_id="credit", resolved=False),
            ],
            city="fort-worth",
        )
        record2 = OutcomeRecord(
            session_id=sid,
            signal_type="barrier_resolved",
            barrier_outcomes=[
                BarrierOutcome(barrier_id="credit", resolved=True, weeks_to_resolve=6),
            ],
            city="fort-worth",
        )
        _record(tracker, db_path, record1)
        _record(tracker, db_path, record2)
        assert tracker.count() == 2
        # get_latest preserves the most recent record
        latest = tracker.get_latest(sid)
        assert latest is not None
        assert latest.barrier_outcomes[0].resolved is True

    def test_get_outcomes_filters_by_city(self, tmp_path: Path) -> None:
        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        _record(tracker, db_path, OutcomeRecord(
            session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            city="fort-worth",
        ))
        _record(tracker, db_path, OutcomeRecord(
            session_id="bbbbbbbb-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            city="montgomery",
        ))
        fw = tracker.get_outcomes_for_city("fort-worth")
        assert len(fw) == 1
        assert fw[0].city == "fort-worth"

    def test_empty_tracker_returns_empty(self, tmp_path: Path) -> None:
        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        assert tracker.count() == 0
        assert tracker.get_outcomes_for_city("fort-worth") == []
