"""Tests for outcome aggregator -- computing community insights from outcomes.

Updated for T12.0a: OutcomeTracker constructor now requires a db_path,
and the aggregator operates over the DB-backed store.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.migrations import runner
from app.modules.outcomes.tracker import OutcomeTracker
from app.modules.outcomes.types import BarrierOutcome, OutcomeRecord


def _prepare_db(tmp_path: Path) -> str:
    """Run migrations on a fresh temp DB and return its path."""
    db_path = str(tmp_path / "aggregator.db")
    runner.apply_pending(db_path)
    return db_path


def _ensure_session(db_path: str, session_id: str) -> None:
    """Insert parent sessions row so FK constraints are satisfied."""
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
    _ensure_session(db_path, record.session_id)
    tracker.record_outcome(record)


def _make_record(
    session_suffix: str,
    barrier_id: str = "criminal_record",
    resolved: bool = True,
    weeks: int | None = 8,
    plan_accuracy: int | None = None,
    city: str = "fort-worth",
) -> OutcomeRecord:
    """Helper to build an outcome record with minimal boilerplate."""
    sid = f"aaaa{session_suffix}-bbbb-cccc-dddd-eeeeeeeeeeee"
    return OutcomeRecord(
        session_id=sid,
        signal_type="barrier_resolved",
        barrier_outcomes=[
            BarrierOutcome(barrier_id=barrier_id, resolved=resolved, weeks_to_resolve=weeks),
        ],
        plan_accuracy=plan_accuracy,
        city=city,
    )


class TestAggregateBarrierInsights:
    """Aggregator computes per-barrier statistics from outcome records."""

    def test_single_resolved_barrier(self, tmp_path: Path) -> None:
        from app.modules.outcomes.aggregator import compute_insights

        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        _record(tracker, db_path, _make_record("0001", "criminal_record", True, 8))
        insights = compute_insights(tracker, "fort-worth")
        assert insights.total_outcomes == 1
        assert len(insights.barrier_insights) == 1
        bi = insights.barrier_insights[0]
        assert bi.barrier_id == "criminal_record"
        assert bi.resolution_count == 1
        assert bi.avg_weeks_to_resolve == 8.0
        assert bi.success_rate == 1.0

    def test_multiple_barriers_aggregated(self, tmp_path: Path) -> None:
        from app.modules.outcomes.aggregator import compute_insights

        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        _record(tracker, db_path, _make_record("0001", "criminal_record", True, 8))
        _record(tracker, db_path, _make_record("0002", "criminal_record", True, 12))
        _record(tracker, db_path, _make_record("0003", "criminal_record", False, None))
        insights = compute_insights(tracker, "fort-worth")
        assert insights.total_outcomes == 3
        bi = [b for b in insights.barrier_insights if b.barrier_id == "criminal_record"][0]
        assert bi.resolution_count == 3
        assert bi.avg_weeks_to_resolve == 10.0  # (8 + 12) / 2 resolved
        assert abs(bi.success_rate - 2 / 3) < 0.01

    def test_mixed_barrier_types(self, tmp_path: Path) -> None:
        from app.modules.outcomes.aggregator import compute_insights

        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        _record(tracker, db_path, _make_record("0001", "criminal_record", True, 8))
        _record(tracker, db_path, _make_record("0002", "credit", True, 4))
        _record(tracker, db_path, _make_record("0003", "transportation", True, 2))
        insights = compute_insights(tracker, "fort-worth")
        assert len(insights.barrier_insights) == 3
        ids = {bi.barrier_id for bi in insights.barrier_insights}
        assert ids == {"criminal_record", "credit", "transportation"}

    def test_empty_tracker_returns_zero_insights(self, tmp_path: Path) -> None:
        from app.modules.outcomes.aggregator import compute_insights

        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        insights = compute_insights(tracker, "fort-worth")
        assert insights.total_outcomes == 0
        assert insights.barrier_insights == []
        assert insights.avg_plan_accuracy == 0.0

    def test_plan_accuracy_averaged(self, tmp_path: Path) -> None:
        from app.modules.outcomes.aggregator import compute_insights

        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        _record(tracker, db_path, _make_record("0001", plan_accuracy=3))
        _record(tracker, db_path, _make_record("0002", plan_accuracy=5))
        _record(tracker, db_path, _make_record("0003", plan_accuracy=2))
        insights = compute_insights(tracker, "fort-worth")
        # avg = (3 + 5 + 2) / 3 = 3.33...
        assert abs(insights.avg_plan_accuracy - 10 / 3) < 0.01

    def test_city_scoping(self, tmp_path: Path) -> None:
        """Insights are scoped to the requested city only."""
        from app.modules.outcomes.aggregator import compute_insights

        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        _record(tracker, db_path, _make_record("0001", city="fort-worth"))
        _record(tracker, db_path, _make_record("0002", city="montgomery"))
        _record(tracker, db_path, _make_record("0003", city="fort-worth"))
        fw_insights = compute_insights(tracker, "fort-worth")
        assert fw_insights.total_outcomes == 2
        al_insights = compute_insights(tracker, "montgomery")
        assert al_insights.total_outcomes == 1

    def test_insights_sorted_by_resolution_count(self, tmp_path: Path) -> None:
        """Barrier insights are sorted by resolution_count descending."""
        from app.modules.outcomes.aggregator import compute_insights

        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        # 3 criminal_record, 1 credit, 2 transportation
        _record(tracker, db_path, _make_record("0001", "criminal_record", True, 8))
        _record(tracker, db_path, _make_record("0002", "criminal_record", True, 10))
        _record(tracker, db_path, _make_record("0003", "criminal_record", False))
        _record(tracker, db_path, _make_record("0004", "credit", True, 4))
        _record(tracker, db_path, _make_record("0005", "transportation", True, 2))
        _record(tracker, db_path, _make_record("0006", "transportation", True, 3))
        insights = compute_insights(tracker, "fort-worth")
        assert insights.barrier_insights[0].barrier_id == "criminal_record"
        assert insights.barrier_insights[0].resolution_count == 3

    def test_multiple_barriers_per_record(self, tmp_path: Path) -> None:
        """A single outcome can report on multiple barriers."""
        from app.modules.outcomes.aggregator import compute_insights

        db_path = _prepare_db(tmp_path)
        tracker = OutcomeTracker(db_path)
        record = OutcomeRecord(
            session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            barrier_outcomes=[
                BarrierOutcome(barrier_id="criminal_record", resolved=True, weeks_to_resolve=8),
                BarrierOutcome(barrier_id="credit", resolved=True, weeks_to_resolve=4),
                BarrierOutcome(barrier_id="housing", resolved=False),
            ],
            city="fort-worth",
        )
        _record(tracker, db_path, record)
        insights = compute_insights(tracker, "fort-worth")
        assert insights.total_outcomes == 1
        assert len(insights.barrier_insights) == 3
