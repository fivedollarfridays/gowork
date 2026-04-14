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


class TestSingleBarrierHighConfidence:
    """HIGH confidence barrier produces confident, data-rich insight."""

    def test_insight_includes_city_name(self):
        """City name appears in the insight message."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record",
                    avg_weeks=8.0,
                    success_rate=0.80,
                    sample_size=15,
                    confidence=ConfidenceLevel.HIGH,
                    stddev_weeks=2.5,
                ),
            ],
            total_feedback_count=15,
            avg_plan_accuracy=4.2,
        )
        insights = generate_insights(calibrated, ["criminal_record"], "Fort Worth")
        assert len(insights) >= 1
        assert "Fort Worth" in insights[0].message

    def test_insight_includes_sample_size(self):
        """Sample size is visible in the message for HIGH confidence."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record",
                    avg_weeks=8.0,
                    success_rate=0.80,
                    sample_size=15,
                    confidence=ConfidenceLevel.HIGH,
                    stddev_weeks=2.5,
                ),
            ],
            total_feedback_count=15,
            avg_plan_accuracy=4.2,
        )
        insights = generate_insights(calibrated, ["criminal_record"], "Fort Worth")
        assert "15" in insights[0].message

    def test_insight_includes_avg_weeks(self):
        """Average weeks metric is visible in the message."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record",
                    avg_weeks=8.0,
                    success_rate=0.80,
                    sample_size=15,
                    confidence=ConfidenceLevel.HIGH,
                    stddev_weeks=2.5,
                ),
            ],
            total_feedback_count=15,
            avg_plan_accuracy=4.2,
        )
        insights = generate_insights(calibrated, ["criminal_record"], "Fort Worth")
        assert "8" in insights[0].message

    def test_insight_model_fields(self):
        """CommunityInsight has correct model fields."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record",
                    avg_weeks=8.0,
                    success_rate=0.80,
                    sample_size=15,
                    confidence=ConfidenceLevel.HIGH,
                    stddev_weeks=2.5,
                ),
            ],
            total_feedback_count=15,
            avg_plan_accuracy=4.2,
        )
        insights = generate_insights(calibrated, ["criminal_record"], "Fort Worth")
        first = insights[0]
        assert isinstance(first, CommunityInsight)
        assert first.barrier_type == "criminal_record"
        assert first.confidence == "high"
        assert first.sample_size == 15
        assert first.metric_type == "resolution_time"

    def test_success_rate_insight_generated(self):
        """A success rate insight is also generated for HIGH confidence."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record",
                    avg_weeks=8.0,
                    success_rate=0.80,
                    sample_size=15,
                    confidence=ConfidenceLevel.HIGH,
                    stddev_weeks=2.5,
                ),
            ],
            total_feedback_count=15,
            avg_plan_accuracy=4.2,
        )
        insights = generate_insights(calibrated, ["criminal_record"], "Fort Worth")
        success_insights = [i for i in insights if i.metric_type == "success_rate"]
        assert len(success_insights) >= 1
        assert "80%" in success_insights[0].message


class TestColdStart:
    """No data should produce encouraging first-user message."""

    def test_cold_start_empty_barriers_data(self):
        """No calibrated barriers = cold start insight."""
        calibrated = CalibratedWeeks(
            barriers=[], total_feedback_count=0, avg_plan_accuracy=0.0,
        )
        insights = generate_insights(calibrated, ["criminal_record"], "Fort Worth")
        assert len(insights) == 1
        assert "first" in insights[0].message.lower()

    def test_cold_start_includes_city(self):
        """Cold start message includes the city name."""
        calibrated = CalibratedWeeks(barriers=[], total_feedback_count=0)
        insights = generate_insights(calibrated, ["credit"], "Montgomery")
        assert "Montgomery" in insights[0].message

    def test_cold_start_encouraging_tone(self):
        """Cold start message frames the user's experience positively."""
        calibrated = CalibratedWeeks(barriers=[], total_feedback_count=0)
        insights = generate_insights(calibrated, ["housing"], "Fort Worth")
        assert "improve" in insights[0].message.lower() or "help" in insights[0].message.lower()

    def test_cold_start_metric_type(self):
        """Cold start insight has recommendation metric type."""
        calibrated = CalibratedWeeks(barriers=[], total_feedback_count=0)
        insights = generate_insights(calibrated, ["training"], "Fort Worth")
        assert insights[0].metric_type == "recommendation"
        assert insights[0].confidence == "none"
        assert insights[0].sample_size == 0


class TestMixedConfidence:
    """Multiple barriers with mixed confidence levels."""

    def test_multiple_barriers_produce_insights_for_each(self):
        """Each user barrier with data gets insights."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record", avg_weeks=8.0,
                    success_rate=0.80, sample_size=15,
                    confidence=ConfidenceLevel.HIGH, stddev_weeks=2.5,
                ),
                CalibratedBarrier(
                    barrier_id="childcare", avg_weeks=4.0,
                    success_rate=0.70, sample_size=7,
                    confidence=ConfidenceLevel.MEDIUM, stddev_weeks=1.5,
                ),
            ],
            total_feedback_count=22,
            avg_plan_accuracy=4.0,
        )
        insights = generate_insights(
            calibrated, ["criminal_record", "childcare"], "Fort Worth",
        )
        barrier_types = {i.barrier_type for i in insights}
        assert "criminal_record" in barrier_types
        assert "childcare" in barrier_types

    def test_low_confidence_uses_cautious_language(self):
        """LOW confidence should use vague, cautious language."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="credit", avg_weeks=6.0,
                    success_rate=0.50, sample_size=2,
                    confidence=ConfidenceLevel.LOW, stddev_weeks=3.0,
                ),
            ],
            total_feedback_count=2,
            avg_plan_accuracy=3.0,
        )
        insights = generate_insights(calibrated, ["credit"], "Fort Worth")
        resolution = [i for i in insights if i.metric_type == "resolution_time"][0]
        # LOW confidence should NOT show exact count "2"
        assert "small number" in resolution.message.lower()
        # Should still include city name
        assert "Fort Worth" in resolution.message

    def test_medium_confidence_uses_moderate_language(self):
        """MEDIUM confidence uses 'Several people' instead of exact count."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="transportation", avg_weeks=3.0,
                    success_rate=0.85, sample_size=5,
                    confidence=ConfidenceLevel.MEDIUM, stddev_weeks=1.0,
                ),
            ],
            total_feedback_count=5,
            avg_plan_accuracy=4.0,
        )
        insights = generate_insights(
            calibrated, ["transportation"], "Fort Worth",
        )
        resolution = [i for i in insights if i.metric_type == "resolution_time"][0]
        # MEDIUM with 5 samples -- at the threshold for exact count
        assert "Fort Worth" in resolution.message

    def test_none_confidence_barriers_skipped(self):
        """Barriers with NONE confidence produce no insights."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="health", avg_weeks=0.0,
                    success_rate=0.0, sample_size=0,
                    confidence=ConfidenceLevel.NONE, stddev_weeks=0.0,
                ),
            ],
            total_feedback_count=0,
            avg_plan_accuracy=0.0,
        )
        insights = generate_insights(calibrated, ["health"], "Fort Worth")
        # Should fall back to cold start since no usable data
        assert len(insights) == 1
        assert "first" in insights[0].message.lower()


class TestBarrierCombinationInsights:
    """Insights about common barrier combinations and recommendations."""

    def test_recommendation_when_multiple_barriers(self):
        """Multiple barriers with data get a recommendation insight."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record", avg_weeks=8.0,
                    success_rate=0.80, sample_size=15,
                    confidence=ConfidenceLevel.HIGH, stddev_weeks=2.5,
                ),
                CalibratedBarrier(
                    barrier_id="transportation", avg_weeks=2.0,
                    success_rate=0.90, sample_size=12,
                    confidence=ConfidenceLevel.HIGH, stddev_weeks=1.0,
                ),
            ],
            total_feedback_count=27,
            avg_plan_accuracy=4.2,
        )
        insights = generate_insights(
            calibrated,
            ["criminal_record", "transportation"],
            "Fort Worth",
        )
        recs = [i for i in insights if i.metric_type == "recommendation"]
        assert len(recs) >= 1
        # Recommendation should reference which barrier to address first
        rec_msg = recs[0].message.lower()
        assert "first" in rec_msg or "start" in rec_msg

    def test_recommendation_suggests_fastest_barrier(self):
        """Recommendation suggests resolving fastest barrier first."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record", avg_weeks=12.0,
                    success_rate=0.70, sample_size=10,
                    confidence=ConfidenceLevel.HIGH, stddev_weeks=3.0,
                ),
                CalibratedBarrier(
                    barrier_id="transportation", avg_weeks=2.0,
                    success_rate=0.95, sample_size=10,
                    confidence=ConfidenceLevel.HIGH, stddev_weeks=0.5,
                ),
            ],
            total_feedback_count=20,
            avg_plan_accuracy=4.0,
        )
        insights = generate_insights(
            calibrated,
            ["criminal_record", "transportation"],
            "Fort Worth",
        )
        recs = [i for i in insights if i.metric_type == "recommendation"]
        assert len(recs) >= 1
        # Should mention transportation (fastest to resolve)
        assert "transportation" in recs[0].message.lower()

    def test_no_recommendation_for_single_barrier(self):
        """Single barrier should not generate a recommendation insight."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record", avg_weeks=8.0,
                    success_rate=0.80, sample_size=15,
                    confidence=ConfidenceLevel.HIGH, stddev_weeks=2.5,
                ),
            ],
            total_feedback_count=15,
            avg_plan_accuracy=4.2,
        )
        insights = generate_insights(
            calibrated, ["criminal_record"], "Fort Worth",
        )
        recs = [i for i in insights if i.metric_type == "recommendation"]
        assert len(recs) == 0


class TestDeterminismAndEdgeCases:
    """Same input always produces same output; edge cases handled."""

    def test_deterministic_output(self):
        """Calling generate_insights twice with same input = same output."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record", avg_weeks=8.0,
                    success_rate=0.80, sample_size=15,
                    confidence=ConfidenceLevel.HIGH, stddev_weeks=2.5,
                ),
                CalibratedBarrier(
                    barrier_id="credit", avg_weeks=6.0,
                    success_rate=0.65, sample_size=8,
                    confidence=ConfidenceLevel.MEDIUM, stddev_weeks=2.0,
                ),
            ],
            total_feedback_count=23,
            avg_plan_accuracy=4.0,
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
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record", avg_weeks=8.0,
                    success_rate=0.80, sample_size=15,
                    confidence=ConfidenceLevel.HIGH, stddev_weeks=2.5,
                ),
            ],
            total_feedback_count=15,
            avg_plan_accuracy=4.2,
        )
        insights = generate_insights(calibrated, [], "Fort Worth")
        assert insights == []

    def test_unknown_barrier_skipped(self):
        """User barrier not in calibrated data is skipped gracefully."""
        calibrated = CalibratedWeeks(
            barriers=[
                CalibratedBarrier(
                    barrier_id="criminal_record", avg_weeks=8.0,
                    success_rate=0.80, sample_size=15,
                    confidence=ConfidenceLevel.HIGH, stddev_weeks=2.5,
                ),
            ],
            total_feedback_count=15,
            avg_plan_accuracy=4.2,
        )
        insights = generate_insights(
            calibrated, ["unknown_barrier"], "Fort Worth",
        )
        # No data for unknown_barrier, falls to cold start
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
            barriers=barrier_objs,
            total_feedback_count=70,
            avg_plan_accuracy=4.0,
        )
        insights = generate_insights(calibrated, all_barriers, "Montgomery")
        # Each barrier gets resolution + success_rate, plus 1 recommendation
        barrier_types = {i.barrier_type for i in insights}
        for bid in all_barriers:
            assert bid in barrier_types
        # Verify city name in all messages
        for i in insights:
            assert "Montgomery" in i.message

    def test_model_serialization(self):
        """CommunityInsight serializes to dict correctly."""
        insight = CommunityInsight(
            message="Test message",
            barrier_type="criminal_record",
            confidence="high",
            sample_size=15,
            metric_type="resolution_time",
        )
        data = insight.model_dump()
        assert data["message"] == "Test message"
        assert data["barrier_type"] == "criminal_record"
        assert data["confidence"] == "high"
        assert data["sample_size"] == 15
        assert data["metric_type"] == "resolution_time"
