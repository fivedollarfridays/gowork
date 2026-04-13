"""Tests for outcome tracker -- recording and storing outcome signals."""

import pytest

from app.modules.outcomes.types import BarrierOutcome, OutcomeRecord


class TestStoreOutcome:
    """Tracker must persist outcome records to in-memory storage."""

    def test_store_single_outcome(self):
        from app.modules.outcomes.tracker import OutcomeTracker

        tracker = OutcomeTracker()
        record = OutcomeRecord(
            session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            barrier_outcomes=[
                BarrierOutcome(barrier_id="criminal_record", resolved=True, weeks_to_resolve=8),
            ],
            city="fort-worth",
        )
        tracker.record_outcome(record)
        assert tracker.count() == 1

    def test_store_multiple_outcomes(self):
        from app.modules.outcomes.tracker import OutcomeTracker

        tracker = OutcomeTracker()
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
            tracker.record_outcome(record)
        assert tracker.count() == 5

    def test_duplicate_session_replaces(self):
        """Second outcome for same session replaces the first."""
        from app.modules.outcomes.tracker import OutcomeTracker

        tracker = OutcomeTracker()
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
        tracker.record_outcome(record1)
        tracker.record_outcome(record2)
        assert tracker.count() == 1
        stored = tracker.get_outcomes_for_city("fort-worth")
        assert stored[0].barrier_outcomes[0].resolved is True

    def test_get_outcomes_filters_by_city(self):
        from app.modules.outcomes.tracker import OutcomeTracker

        tracker = OutcomeTracker()
        tracker.record_outcome(OutcomeRecord(
            session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            city="fort-worth",
        ))
        tracker.record_outcome(OutcomeRecord(
            session_id="bbbbbbbb-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            city="montgomery",
        ))
        fw = tracker.get_outcomes_for_city("fort-worth")
        assert len(fw) == 1
        assert fw[0].city == "fort-worth"

    def test_empty_tracker_returns_empty(self):
        from app.modules.outcomes.tracker import OutcomeTracker

        tracker = OutcomeTracker()
        assert tracker.count() == 0
        assert tracker.get_outcomes_for_city("fort-worth") == []
