"""Tests for DB-backed OutcomeTracker (T12.0a).

Covers append-only insert semantics, chronological ordering,
cross-session aggregates, process-restart durability, CASCADE on
session delete, and auto-populated created_at.

Each test uses a fresh SQLite file under pytest's tmp_path so nothing
touches the production database. The schema is bootstrapped via the
m002 migration runner so we exercise the real table definitions.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.migrations import runner
from app.modules.outcomes.tracker import OutcomeTracker
from app.modules.outcomes.types import BarrierOutcome, OutcomeRecord


# -------------------- Fixtures --------------------


_SESSION_ID_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_ID_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
_SESSION_ID_C = "cccccccc-dddd-eeee-ffff-000000000000"


def _init_db(tmp_path: Path) -> str:
    """Create a fresh migrated DB file and return its path as a string."""
    db_path = str(tmp_path / "outcomes.db")
    runner.apply_pending(db_path)
    _seed_sessions(db_path, [_SESSION_ID_A, _SESSION_ID_B, _SESSION_ID_C])
    return db_path


def _seed_sessions(db_path: str, session_ids: list[str]) -> None:
    """Seed rows in the `sessions` table so FK constraints are satisfied."""
    conn = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        for sid in session_ids:
            conn.execute(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (sid, now, "[]", now),
            )
        conn.commit()
    finally:
        conn.close()


def _make_record(
    session_id: str = _SESSION_ID_A,
    *,
    signal_type: str = "barrier_resolved",
    city: str = "fort-worth",
    barriers: list[BarrierOutcome] | None = None,
    plan_accuracy: int | None = None,
    created_at: datetime | None = None,
) -> OutcomeRecord:
    """Build an OutcomeRecord with defaults suitable for most tests."""
    return OutcomeRecord(
        session_id=session_id,
        signal_type=signal_type,
        barrier_outcomes=barriers or [],
        plan_accuracy=plan_accuracy,
        city=city,
        created_at=created_at.isoformat() if created_at else None,
    )


# -------------------- Append-only semantics --------------------


def test_record_outcome_inserts_not_upserts(tmp_path: Path) -> None:
    """Two records for the same session both persist; no upsert."""
    db_path = _init_db(tmp_path)
    tracker = OutcomeTracker(db_path)

    tracker.record_outcome(_make_record(
        barriers=[BarrierOutcome(barrier_id="credit", resolved=False)],
    ))
    tracker.record_outcome(_make_record(
        barriers=[BarrierOutcome(barrier_id="credit", resolved=True, weeks_to_resolve=6)],
    ))

    stored = tracker.list_by_session(_SESSION_ID_A)
    assert len(stored) == 2
    # Both records preserved — first resolved=False, second resolved=True
    resolutions = {r.barrier_outcomes[0].resolved for r in stored}
    assert resolutions == {False, True}


def test_list_by_session_chronological(tmp_path: Path) -> None:
    """Records are returned in ascending created_at order regardless of insert order."""
    db_path = _init_db(tmp_path)
    tracker = OutcomeTracker(db_path)

    base = datetime(2026, 4, 23, 12, 0, 0, tzinfo=timezone.utc)
    # Insert out-of-order
    tracker.record_outcome(_make_record(created_at=base + timedelta(hours=2)))
    tracker.record_outcome(_make_record(created_at=base))
    tracker.record_outcome(_make_record(created_at=base + timedelta(hours=1)))

    stored = tracker.list_by_session(_SESSION_ID_A)
    assert len(stored) == 3
    timestamps = [r.created_at for r in stored]
    assert timestamps == sorted(timestamps)


# -------------------- Cross-session aggregates --------------------


def test_list_recent_filters_by_city_and_type(tmp_path: Path) -> None:
    """list_recent filters on city and optional event_type."""
    db_path = _init_db(tmp_path)
    tracker = OutcomeTracker(db_path)

    tracker.record_outcome(_make_record(
        session_id=_SESSION_ID_A, city="fort-worth", signal_type="barrier_resolved",
    ))
    tracker.record_outcome(_make_record(
        session_id=_SESSION_ID_B, city="fort-worth", signal_type="plan_followed",
    ))
    tracker.record_outcome(_make_record(
        session_id=_SESSION_ID_C, city="montgomery", signal_type="barrier_resolved",
    ))

    fw_all = tracker.list_recent(city="fort-worth")
    assert len(fw_all) == 2
    assert all(r.city == "fort-worth" for r in fw_all)

    fw_resolved = tracker.list_recent(city="fort-worth", event_type="barrier_resolved")
    assert len(fw_resolved) == 1
    assert fw_resolved[0].signal_type == "barrier_resolved"


def test_list_recent_since_filter(tmp_path: Path) -> None:
    """list_recent respects `since` cutoff, excluding older records."""
    db_path = _init_db(tmp_path)
    tracker = OutcomeTracker(db_path)

    old = datetime(2026, 1, 1, tzinfo=timezone.utc)
    recent = datetime(2026, 4, 23, tzinfo=timezone.utc)
    tracker.record_outcome(_make_record(created_at=old))
    tracker.record_outcome(_make_record(created_at=recent))

    cutoff = datetime(2026, 3, 1, tzinfo=timezone.utc)
    results = tracker.list_recent(city="fort-worth", since=cutoff)
    assert len(results) == 1
    assert results[0].created_at >= cutoff.isoformat()


# -------------------- Durability --------------------


def test_process_restart_durability(tmp_path: Path) -> None:
    """Records survive across tracker re-instantiation (new connection)."""
    db_path = _init_db(tmp_path)

    tracker_a = OutcomeTracker(db_path)
    tracker_a.record_outcome(_make_record(
        barriers=[BarrierOutcome(barrier_id="credit", resolved=True, weeks_to_resolve=4)],
    ))

    # Second tracker instance = fresh connection
    tracker_b = OutcomeTracker(db_path)
    stored = tracker_b.list_by_session(_SESSION_ID_A)
    assert len(stored) == 1
    assert stored[0].barrier_outcomes[0].barrier_id == "credit"
    assert stored[0].barrier_outcomes[0].weeks_to_resolve == 4


# -------------------- get_latest --------------------


def test_get_latest_returns_most_recent(tmp_path: Path) -> None:
    """get_latest returns the most recent record for the session."""
    db_path = _init_db(tmp_path)
    tracker = OutcomeTracker(db_path)

    base = datetime(2026, 4, 1, tzinfo=timezone.utc)
    tracker.record_outcome(_make_record(
        created_at=base,
        barriers=[BarrierOutcome(barrier_id="credit", resolved=False)],
    ))
    tracker.record_outcome(_make_record(
        created_at=base + timedelta(days=10),
        barriers=[BarrierOutcome(barrier_id="credit", resolved=True, weeks_to_resolve=2)],
    ))
    tracker.record_outcome(_make_record(
        created_at=base + timedelta(days=5),
        barriers=[BarrierOutcome(barrier_id="credit", resolved=False)],
    ))

    latest = tracker.get_latest(_SESSION_ID_A)
    assert latest is not None
    assert latest.barrier_outcomes[0].resolved is True
    assert latest.barrier_outcomes[0].weeks_to_resolve == 2


def test_get_latest_empty_returns_none(tmp_path: Path) -> None:
    """get_latest returns None when no records exist for the session."""
    db_path = _init_db(tmp_path)
    tracker = OutcomeTracker(db_path)
    assert tracker.get_latest(_SESSION_ID_A) is None


# -------------------- CASCADE --------------------


def test_cascade_on_session_delete(tmp_path: Path) -> None:
    """Deleting the parent session removes associated outcomes_records rows."""
    db_path = _init_db(tmp_path)
    tracker = OutcomeTracker(db_path)

    tracker.record_outcome(_make_record(session_id=_SESSION_ID_A))
    tracker.record_outcome(_make_record(session_id=_SESSION_ID_A))
    tracker.record_outcome(_make_record(session_id=_SESSION_ID_B))

    # Verify baseline
    assert len(tracker.list_by_session(_SESSION_ID_A)) == 2
    assert len(tracker.list_by_session(_SESSION_ID_B)) == 1

    # CASCADE requires foreign_keys pragma ON
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM sessions WHERE id = ?", (_SESSION_ID_A,))
        conn.commit()
    finally:
        conn.close()

    # Session A's outcomes gone, B intact
    assert tracker.list_by_session(_SESSION_ID_A) == []
    assert len(tracker.list_by_session(_SESSION_ID_B)) == 1


# -------------------- Auto-populate created_at --------------------


def test_auto_populates_created_at(tmp_path: Path) -> None:
    """When caller provides no created_at, an ISO timestamp is written."""
    db_path = _init_db(tmp_path)
    tracker = OutcomeTracker(db_path)

    before = datetime.now(timezone.utc)
    tracker.record_outcome(OutcomeRecord(
        session_id=_SESSION_ID_A,
        signal_type="barrier_resolved",
        city="fort-worth",
    ))
    after = datetime.now(timezone.utc)

    stored = tracker.list_by_session(_SESSION_ID_A)
    assert len(stored) == 1
    # ISO string round-trips
    parsed = datetime.fromisoformat(stored[0].created_at)
    assert before <= parsed <= after


# -------------------- Barriers snapshot passthrough --------------------


def test_barriers_snapshot_persisted(tmp_path: Path) -> None:
    """barrier_outcomes payload survives the round trip."""
    db_path = _init_db(tmp_path)
    tracker = OutcomeTracker(db_path)

    tracker.record_outcome(_make_record(
        barriers=[
            BarrierOutcome(barrier_id="credit", resolved=True, weeks_to_resolve=4),
            BarrierOutcome(barrier_id="transportation", resolved=False),
        ],
        plan_accuracy=4,
    ))

    stored = tracker.list_by_session(_SESSION_ID_A)
    assert len(stored) == 1
    rec = stored[0]
    assert rec.plan_accuracy == 4
    ids = {bo.barrier_id for bo in rec.barrier_outcomes}
    assert ids == {"credit", "transportation"}
