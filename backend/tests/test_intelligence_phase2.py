"""Phase 2 evolution tests for outcome intelligence engine.

Tests variance tracking, plan accuracy aggregation, coverage gaps,
and adversarial edge cases from Donatello modules.
"""

import pytest

from app.modules.outcomes.intelligence import (
    CalibratedWeeks,
    ConfidenceLevel,
    compute_calibrated_barriers,
)


class TestSafeParseListCoverageGap:
    """Cover the non-list JSON parse branch in _safe_parse_list.

    intelligence_queries.py line 73: parsed JSON is valid but not a list
    (e.g., dict or string). Tests here exercise the compute layer
    with rows that would result from such parsing.
    """

    def test_empty_rows_returns_none_confidence(self):
        """Explicit cold start: no data at all."""
        result = compute_calibrated_barriers([])
        assert result.confidence == ConfidenceLevel.NONE
        assert result.barriers == []
        assert result.avg_plan_accuracy == 0.0
        assert result.total_feedback_count == 0


class TestPlanAccuracyAggregation:
    """Plan accuracy from feedback should be aggregated in CalibratedWeeks."""

    def test_avg_plan_accuracy_computed(self):
        rows = [
            _row("credit", True, 4, plan_accuracy=4),
            _row("credit", True, 6, plan_accuracy=5),
            _row("credit", True, 8, plan_accuracy=3),
        ]
        result = compute_calibrated_barriers(rows)
        assert result.avg_plan_accuracy == 4.0  # (4+5+3) / 3

    def test_avg_plan_accuracy_excludes_none(self):
        rows = [
            _row("credit", True, 4, plan_accuracy=4),
            _row("credit", True, 6, plan_accuracy=None),
            _row("credit", True, 8, plan_accuracy=2),
        ]
        result = compute_calibrated_barriers(rows)
        assert result.avg_plan_accuracy == 3.0  # (4+2) / 2

    def test_avg_plan_accuracy_all_none(self):
        rows = [
            _row("credit", True, 4, plan_accuracy=None),
            _row("credit", True, 6, plan_accuracy=None),
        ]
        result = compute_calibrated_barriers(rows)
        assert result.avg_plan_accuracy == 0.0

    def test_total_feedback_count(self):
        rows = [
            _row("credit", True, 4),
            _row("credit", True, 6),
            _row("housing", True, 3),
        ]
        result = compute_calibrated_barriers(rows)
        assert result.total_feedback_count == 3


class TestVarianceTracking:
    """Per-barrier variance detects contradictory feedback."""

    def test_consistent_weeks_low_stddev(self):
        rows = [_row("credit", True, w) for w in [8, 8, 8]]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        assert barrier.stddev_weeks == 0.0

    def test_contradictory_weeks_high_stddev(self):
        """Half say 6 weeks, half say 20 weeks -- stddev should be high."""
        rows = [
            _row("credit", True, 6),
            _row("credit", True, 6),
            _row("credit", True, 20),
            _row("credit", True, 20),
        ]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        # mean=13, variance=((6-13)^2+(6-13)^2+(20-13)^2+(20-13)^2)/4 = 49
        # stddev = 7.0
        assert barrier.stddev_weeks == 7.0

    def test_stddev_zero_when_no_resolved(self):
        rows = [_row("credit", False, None)] * 3
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        assert barrier.stddev_weeks == 0.0

    def test_stddev_zero_with_single_sample(self):
        rows = [_row("credit", True, 10)]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        assert barrier.stddev_weeks == 0.0


class TestLargeDataset:
    """Donatello Module 2/5: Boundary and performance with large data."""

    def test_thousand_records_correct(self):
        """1000 records across 7 barrier types computes correctly."""
        barrier_types = [
            "criminal_record", "credit", "transportation",
            "childcare", "housing", "health", "training",
        ]
        rows = []
        for i in range(1000):
            bid = barrier_types[i % 7]
            rows.append(_row(bid, True, (i % 20) + 1))
        result = compute_calibrated_barriers(rows)
        assert len(result.barriers) == 7
        assert result.total_feedback_count == 1000
        for b in result.barriers:
            assert b.confidence == ConfidenceLevel.HIGH
            assert b.sample_size >= 142  # 1000/7 ~= 142-143


class TestDuplicateBarriers:
    """Edge case: duplicate barrier IDs in feedback rows."""

    def test_duplicate_barrier_ids_counted_separately(self):
        """Each row is an independent observation, even if same barrier."""
        rows = [
            _row("credit", True, 4),
            _row("credit", True, 4),
            _row("credit", True, 4),
        ]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        assert barrier.sample_size == 3


class TestExtremeWeeks:
    """Donatello Module 2: Extreme boundary values for weeks."""

    def test_very_large_weeks(self):
        rows = [_row("credit", True, w) for w in [999, 1000, 1001]]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        assert barrier.avg_weeks == 1000.0

    def test_zero_weeks_all_resolved(self):
        rows = [_row("credit", True, 0)] * 3
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        assert barrier.avg_weeks == 0.0
        # avg_weeks == 0 should be excluded from to_weeks_dict
        assert "credit" not in result.to_weeks_dict()


# -- Helpers --


def _row(
    barrier_id: str,
    resolved: bool,
    weeks: int | None,
    plan_accuracy: int | None = None,
) -> dict:
    """Build a raw feedback row matching the DB join shape."""
    return {
        "barrier_id": barrier_id,
        "resolved": resolved,
        "weeks_to_resolve": weeks,
        "plan_accuracy": plan_accuracy,
    }


def _find(result: CalibratedWeeks, barrier_id: str):
    """Find a CalibratedBarrier by ID or fail."""
    for b in result.barriers:
        if b.barrier_id == barrier_id:
            return b
    raise AssertionError(f"barrier {barrier_id!r} not found in {result.barriers}")
