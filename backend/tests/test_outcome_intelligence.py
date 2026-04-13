"""Tests for outcome intelligence engine — N+1 feedback loop.

Cycle 1: Core computation from raw feedback data.
"""

import pytest

from app.modules.outcomes.intelligence import (
    CalibratedBarrier,
    CalibratedWeeks,
    ConfidenceLevel,
    compute_calibrated_barriers,
)


class TestConfidenceLevel:
    """Confidence level assigned based on sample size."""

    def test_zero_samples_returns_none_confidence(self):
        result = compute_calibrated_barriers([])
        assert result.confidence == ConfidenceLevel.NONE

    def test_one_sample_returns_low_confidence(self):
        rows = [_row("criminal_record", True, 8)]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "criminal_record")
        assert barrier.confidence == ConfidenceLevel.LOW

    def test_two_samples_returns_low_confidence(self):
        rows = [_row("criminal_record", True, 8), _row("criminal_record", True, 10)]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "criminal_record")
        assert barrier.confidence == ConfidenceLevel.LOW

    def test_three_samples_returns_medium_confidence(self):
        rows = [_row("criminal_record", True, w) for w in [6, 8, 10]]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "criminal_record")
        assert barrier.confidence == ConfidenceLevel.MEDIUM

    def test_ten_samples_returns_high_confidence(self):
        rows = [_row("criminal_record", True, w) for w in range(3, 13)]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "criminal_record")
        assert barrier.confidence == ConfidenceLevel.HIGH


class TestCalibratedBarrierStats:
    """Per-barrier statistics from feedback rows."""

    def test_avg_weeks_computed(self):
        rows = [_row("credit", True, 4), _row("credit", True, 8)]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        assert barrier.avg_weeks == 6.0

    def test_success_rate_computed(self):
        rows = [
            _row("credit", True, 4),
            _row("credit", True, 8),
            _row("credit", False, None),
        ]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        assert abs(barrier.success_rate - 2 / 3) < 0.01

    def test_sample_size_tracked(self):
        rows = [_row("credit", True, 4)] * 5
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "credit")
        assert barrier.sample_size == 5

    def test_unresolved_barriers_excluded_from_avg_weeks(self):
        """Unresolved barriers (weeks=None) don't affect avg_weeks."""
        rows = [
            _row("housing", True, 6),
            _row("housing", False, None),
            _row("housing", True, 10),
        ]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "housing")
        assert barrier.avg_weeks == 8.0  # (6+10)/2

    def test_multiple_barrier_types_separated(self):
        rows = [
            _row("credit", True, 4),
            _row("transportation", True, 2),
            _row("credit", True, 8),
        ]
        result = compute_calibrated_barriers(rows)
        credit = _find(result, "credit")
        transport = _find(result, "transportation")
        assert credit.avg_weeks == 6.0
        assert transport.avg_weeks == 2.0

    def test_all_unresolved_yields_zero_avg_weeks(self):
        rows = [_row("health", False, None), _row("health", False, None)]
        result = compute_calibrated_barriers(rows)
        barrier = _find(result, "health")
        assert barrier.avg_weeks == 0.0
        assert barrier.success_rate == 0.0


class TestCalibratedWeeks:
    """CalibratedWeeks dict for barrier_sequencer integration."""

    def test_returns_calibrated_weeks_dict(self):
        rows = [_row("criminal_record", True, w) for w in [6, 8, 10]]
        result = compute_calibrated_barriers(rows)
        cw = result.to_weeks_dict()
        assert isinstance(cw, dict)
        assert "criminal_record" in cw
        assert cw["criminal_record"] == 8  # avg=8.0, rounded to int

    def test_low_confidence_excluded_from_weeks_dict(self):
        """Only MEDIUM+ confidence barriers are included in the weeks dict."""
        rows = [_row("credit", True, 4)]  # 1 sample -> LOW
        result = compute_calibrated_barriers(rows)
        cw = result.to_weeks_dict()
        assert "credit" not in cw

    def test_zero_avg_weeks_excluded_from_weeks_dict(self):
        rows = [_row("health", False, None)] * 5
        result = compute_calibrated_barriers(rows)
        cw = result.to_weeks_dict()
        assert "health" not in cw

    def test_weeks_rounded_to_int(self):
        rows = [_row("transportation", True, w) for w in [1, 2, 3]]
        result = compute_calibrated_barriers(rows)
        cw = result.to_weeks_dict()
        assert cw["transportation"] == 2  # avg=2.0


# ── Helpers ──


def _row(barrier_id: str, resolved: bool, weeks: int | None) -> dict:
    """Build a raw feedback row matching the DB join shape."""
    return {
        "barrier_id": barrier_id,
        "resolved": resolved,
        "weeks_to_resolve": weeks,
    }


def _find(result: CalibratedWeeks, barrier_id: str) -> CalibratedBarrier:
    """Find a CalibratedBarrier by ID or fail."""
    for b in result.barriers:
        if b.barrier_id == barrier_id:
            return b
    raise AssertionError(f"barrier {barrier_id!r} not found in {result.barriers}")
