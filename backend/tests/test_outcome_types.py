"""Tests for outcome tracking types -- Pydantic models and enums."""

import pytest
from pydantic import ValidationError


class TestOutcomeSignalType:
    """Outcome signal types must be a strict enum."""

    def test_valid_signal_types(self):
        from app.modules.outcomes.types import OutcomeSignalType

        assert OutcomeSignalType.BARRIER_RESOLVED == "barrier_resolved"
        assert OutcomeSignalType.PLAN_FOLLOWED == "plan_followed"
        assert OutcomeSignalType.RESOURCE_EFFECTIVE == "resource_effective"

    def test_signal_type_is_string_enum(self):
        from app.modules.outcomes.types import OutcomeSignalType

        assert isinstance(OutcomeSignalType.BARRIER_RESOLVED, str)


class TestBarrierOutcome:
    """Barrier resolution outcome model validation."""

    def test_valid_barrier_outcome(self):
        from app.modules.outcomes.types import BarrierOutcome

        outcome = BarrierOutcome(
            barrier_id="criminal_record",
            resolved=True,
            weeks_to_resolve=8,
        )
        assert outcome.barrier_id == "criminal_record"
        assert outcome.resolved is True
        assert outcome.weeks_to_resolve == 8

    def test_barrier_outcome_defaults(self):
        from app.modules.outcomes.types import BarrierOutcome

        outcome = BarrierOutcome(barrier_id="credit")
        assert outcome.resolved is False
        assert outcome.weeks_to_resolve is None

    def test_barrier_outcome_rejects_negative_weeks(self):
        from app.modules.outcomes.types import BarrierOutcome

        with pytest.raises(ValidationError):
            BarrierOutcome(barrier_id="credit", weeks_to_resolve=-1)

    def test_barrier_outcome_rejects_empty_id(self):
        from app.modules.outcomes.types import BarrierOutcome

        with pytest.raises(ValidationError):
            BarrierOutcome(barrier_id="")


class TestOutcomeRecord:
    """Full outcome record model validation."""

    def test_valid_outcome_record(self):
        from app.modules.outcomes.types import BarrierOutcome, OutcomeRecord

        record = OutcomeRecord(
            session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            signal_type="barrier_resolved",
            barrier_outcomes=[
                BarrierOutcome(barrier_id="criminal_record", resolved=True, weeks_to_resolve=8),
            ],
            plan_accuracy=3,
            city="fort-worth",
        )
        assert record.session_id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        assert len(record.barrier_outcomes) == 1
        assert record.city == "fort-worth"

    def test_outcome_record_rejects_invalid_session_id(self):
        from app.modules.outcomes.types import OutcomeRecord

        with pytest.raises(ValidationError):
            OutcomeRecord(
                session_id="not-a-uuid",
                signal_type="barrier_resolved",
            )

    def test_plan_accuracy_range(self):
        from app.modules.outcomes.types import OutcomeRecord

        with pytest.raises(ValidationError):
            OutcomeRecord(
                session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                signal_type="plan_followed",
                plan_accuracy=0,
            )
        with pytest.raises(ValidationError):
            OutcomeRecord(
                session_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                signal_type="plan_followed",
                plan_accuracy=6,
            )


class TestAggregateInsight:
    """Aggregate insight response model."""

    def test_barrier_insight_model(self):
        from app.modules.outcomes.types import BarrierInsight

        insight = BarrierInsight(
            barrier_id="criminal_record",
            resolution_count=50,
            avg_weeks_to_resolve=8.5,
            success_rate=0.72,
        )
        assert insight.barrier_id == "criminal_record"
        assert insight.resolution_count == 50
        assert insight.avg_weeks_to_resolve == 8.5
        assert insight.success_rate == 0.72

    def test_community_insights_model(self):
        from app.modules.outcomes.types import BarrierInsight, CommunityInsights

        insights = CommunityInsights(
            total_outcomes=100,
            barrier_insights=[
                BarrierInsight(
                    barrier_id="criminal_record",
                    resolution_count=50,
                    avg_weeks_to_resolve=8.5,
                    success_rate=0.72,
                ),
            ],
            avg_plan_accuracy=2.5,
            city="fort-worth",
        )
        assert insights.total_outcomes == 100
        assert len(insights.barrier_insights) == 1
        assert insights.avg_plan_accuracy == 2.5
