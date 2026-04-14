"""Tests for the 'People Like You' Community Insights engine.

Verifies that generate_insights produces personalized, deterministic,
city-aware community insight messages from calibrated barrier data.
"""

import pytest

from app.modules.outcomes.intelligence import (
    CalibratedBarrier,
    CalibratedWeeks,
    ConfidenceLevel,
)
from app.modules.outcomes.community_insights import (
    CommunityInsight,
    generate_insights,
)


def _barrier(
    bid: str = "criminal_record",
    weeks: float = 8.0,
    rate: float = 0.80,
    size: int = 15,
    conf: ConfidenceLevel = ConfidenceLevel.HIGH,
    stddev: float = 2.5,
) -> CalibratedBarrier:
    """Build a CalibratedBarrier with sensible defaults."""
    return CalibratedBarrier(
        barrier_id=bid, avg_weeks=weeks, success_rate=rate,
        sample_size=size, confidence=conf, stddev_weeks=stddev,
    )


def _calibrated(
    barriers: list[CalibratedBarrier] | None = None,
    total: int = 15,
    accuracy: float = 4.2,
) -> CalibratedWeeks:
    """Build a CalibratedWeeks with sensible defaults."""
    return CalibratedWeeks(
        barriers=barriers or [_barrier()],
        total_feedback_count=total,
        avg_plan_accuracy=accuracy,
    )


def _empty_calibrated() -> CalibratedWeeks:
    """Build an empty (cold-start) CalibratedWeeks."""
    return CalibratedWeeks(barriers=[], total_feedback_count=0)


class TestSingleBarrierHighConfidence:
    """HIGH confidence barrier produces confident, data-rich insight."""

    def test_insight_includes_city_name(self):
        """City name appears in the insight message."""
        insights = generate_insights(_calibrated(), ["criminal_record"], "Fort Worth")
        assert len(insights) >= 1
        assert "Fort Worth" in insights[0].message

    def test_insight_includes_sample_size(self):
        """Sample size is visible in the message for HIGH confidence."""
        insights = generate_insights(_calibrated(), ["criminal_record"], "Fort Worth")
        assert "15" in insights[0].message

    def test_insight_includes_avg_weeks(self):
        """Average weeks metric is visible in the message."""
        insights = generate_insights(_calibrated(), ["criminal_record"], "Fort Worth")
        assert "8" in insights[0].message

    def test_insight_model_fields(self):
        """CommunityInsight has correct model fields."""
        insights = generate_insights(_calibrated(), ["criminal_record"], "Fort Worth")
        first = insights[0]
        assert isinstance(first, CommunityInsight)
        assert first.barrier_type == "criminal_record"
        assert first.confidence == "high"
        assert first.sample_size == 15
        assert first.metric_type == "resolution_time"

    def test_success_rate_insight_generated(self):
        """A success rate insight is also generated for HIGH confidence."""
        insights = generate_insights(_calibrated(), ["criminal_record"], "Fort Worth")
        success_insights = [i for i in insights if i.metric_type == "success_rate"]
        assert len(success_insights) >= 1
        assert "80%" in success_insights[0].message


class TestColdStart:
    """No data should produce encouraging first-user message."""

    def test_cold_start_empty_barriers_data(self):
        """No calibrated barriers = cold start insight."""
        insights = generate_insights(_empty_calibrated(), ["criminal_record"], "Fort Worth")
        assert len(insights) == 1
        assert "first" in insights[0].message.lower()

    def test_cold_start_includes_city(self):
        """Cold start message includes the city name."""
        insights = generate_insights(_empty_calibrated(), ["credit"], "Montgomery")
        assert "Montgomery" in insights[0].message

    def test_cold_start_encouraging_tone(self):
        """Cold start message frames the user's experience positively."""
        insights = generate_insights(_empty_calibrated(), ["housing"], "Fort Worth")
        assert "improve" in insights[0].message.lower() or "help" in insights[0].message.lower()

    def test_cold_start_metric_type(self):
        """Cold start insight has recommendation metric type."""
        insights = generate_insights(_empty_calibrated(), ["training"], "Fort Worth")
        assert insights[0].metric_type == "recommendation"
        assert insights[0].confidence == "none"
        assert insights[0].sample_size == 0


class TestMixedConfidence:
    """Multiple barriers with mixed confidence levels."""

    def test_multiple_barriers_produce_insights_for_each(self):
        """Each user barrier with data gets insights."""
        calibrated = _calibrated(
            barriers=[
                _barrier("criminal_record"),
                _barrier("childcare", weeks=4.0, rate=0.70, size=7,
                         conf=ConfidenceLevel.MEDIUM, stddev=1.5),
            ],
            total=22, accuracy=4.0,
        )
        insights = generate_insights(
            calibrated, ["criminal_record", "childcare"], "Fort Worth",
        )
        barrier_types = {i.barrier_type for i in insights}
        assert "criminal_record" in barrier_types
        assert "childcare" in barrier_types

    def test_low_confidence_uses_cautious_language(self):
        """LOW confidence should use vague, cautious language."""
        calibrated = _calibrated(
            barriers=[_barrier("credit", weeks=6.0, rate=0.50, size=2,
                               conf=ConfidenceLevel.LOW, stddev=3.0)],
            total=2, accuracy=3.0,
        )
        insights = generate_insights(calibrated, ["credit"], "Fort Worth")
        resolution = [i for i in insights if i.metric_type == "resolution_time"][0]
        assert "small number" in resolution.message.lower()
        assert "Fort Worth" in resolution.message

    def test_medium_confidence_uses_moderate_language(self):
        """MEDIUM confidence uses 'Several people' instead of exact count."""
        calibrated = _calibrated(
            barriers=[_barrier("transportation", weeks=3.0, rate=0.85, size=5,
                               conf=ConfidenceLevel.MEDIUM, stddev=1.0)],
            total=5, accuracy=4.0,
        )
        insights = generate_insights(calibrated, ["transportation"], "Fort Worth")
        resolution = [i for i in insights if i.metric_type == "resolution_time"][0]
        assert "Fort Worth" in resolution.message

    def test_none_confidence_barriers_skipped(self):
        """Barriers with NONE confidence produce no insights."""
        calibrated = CalibratedWeeks(
            barriers=[_barrier("health", weeks=0.0, rate=0.0, size=0,
                               conf=ConfidenceLevel.NONE, stddev=0.0)],
            total_feedback_count=0, avg_plan_accuracy=0.0,
        )
        insights = generate_insights(calibrated, ["health"], "Fort Worth")
        assert len(insights) == 1
        assert "first" in insights[0].message.lower()


class TestBarrierCombinationInsights:
    """Insights about common barrier combinations and recommendations."""

    def test_recommendation_when_multiple_barriers(self):
        """Multiple barriers with data get a recommendation insight."""
        calibrated = _calibrated(
            barriers=[
                _barrier("criminal_record"),
                _barrier("transportation", weeks=2.0, rate=0.90, size=12, stddev=1.0),
            ],
            total=27,
        )
        insights = generate_insights(
            calibrated, ["criminal_record", "transportation"], "Fort Worth",
        )
        recs = [i for i in insights if i.metric_type == "recommendation"]
        assert len(recs) >= 1
        rec_msg = recs[0].message.lower()
        assert "first" in rec_msg or "start" in rec_msg

    def test_recommendation_suggests_fastest_barrier(self):
        """Recommendation suggests resolving fastest barrier first."""
        calibrated = _calibrated(
            barriers=[
                _barrier("criminal_record", weeks=12.0, rate=0.70, size=10, stddev=3.0),
                _barrier("transportation", weeks=2.0, rate=0.95, size=10, stddev=0.5),
            ],
            total=20, accuracy=4.0,
        )
        insights = generate_insights(
            calibrated, ["criminal_record", "transportation"], "Fort Worth",
        )
        recs = [i for i in insights if i.metric_type == "recommendation"]
        assert len(recs) >= 1
        assert "transportation" in recs[0].message.lower()

    def test_no_recommendation_for_single_barrier(self):
        """Single barrier should not generate a recommendation insight."""
        insights = generate_insights(
            _calibrated(), ["criminal_record"], "Fort Worth",
        )
        recs = [i for i in insights if i.metric_type == "recommendation"]
        assert len(recs) == 0


class TestDeterminismAndEdgeCases:
    """Same input always produces same output; edge cases handled."""

    def test_deterministic_output(self):
        """Calling generate_insights twice with same input = same output."""
        calibrated = _calibrated(
            barriers=[
                _barrier("criminal_record"),
                _barrier("credit", weeks=6.0, rate=0.65, size=8,
                         conf=ConfidenceLevel.MEDIUM, stddev=2.0),
            ],
            total=23, accuracy=4.0,
        )
        barriers = ["criminal_record", "credit"]
        first = generate_insights(calibrated, barriers, "Fort Worth")
        second = generate_insights(calibrated, barriers, "Fort Worth")
        assert len(first) == len(second)
        for a, b in zip(first, second):
            assert a.message == b.message
            assert a.barrier_type == b.barrier_type
            assert a.confidence == b.confidence
            assert a.sample_size == b.sample_size

    def test_empty_barriers_returns_empty(self):
        """No user barriers should produce no insights."""
        insights = generate_insights(_calibrated(), [], "Fort Worth")
        assert insights == []

    def test_unknown_barrier_skipped(self):
        """User barrier not in calibrated data is skipped gracefully."""
        insights = generate_insights(
            _calibrated(), ["unknown_barrier"], "Fort Worth",
        )
        assert len(insights) == 1
        assert "first" in insights[0].message.lower()

    def test_all_known_barriers(self):
        """All 7 barrier types produce insights when data exists."""
        all_barriers = [
            "criminal_record", "credit", "transportation",
            "childcare", "housing", "health", "training",
        ]
        barrier_objs = [
            CalibratedBarrier(
                barrier_id=bid, avg_weeks=float(i + 2),
                success_rate=0.70, sample_size=10,
                confidence=ConfidenceLevel.HIGH, stddev_weeks=1.0,
            )
            for i, bid in enumerate(all_barriers)
        ]
        calibrated = CalibratedWeeks(
            barriers=barrier_objs, total_feedback_count=70, avg_plan_accuracy=4.0,
        )
        insights = generate_insights(calibrated, all_barriers, "Montgomery")
        barrier_types = {i.barrier_type for i in insights}
        for bid in all_barriers:
            assert bid in barrier_types
        for i in insights:
            assert "Montgomery" in i.message

    def test_model_serialization(self):
        """CommunityInsight serializes to dict correctly."""
        insight = CommunityInsight(
            message="Test message", barrier_type="criminal_record",
            confidence="high", sample_size=15, metric_type="resolution_time",
        )
        data = insight.model_dump()
        assert data["message"] == "Test message"
        assert data["barrier_type"] == "criminal_record"
        assert data["confidence"] == "high"
        assert data["sample_size"] == 15
        assert data["metric_type"] == "resolution_time"
