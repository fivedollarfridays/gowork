"""Tests for ScoringContext dataclass — bundles user-level scoring parameters."""

from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.pvs_scorer import compute_pvs, rank_all_jobs
from app.modules.matching.types import (
    AvailableHours,
    BarrierType,
    ScoringContext,
)


class TestScoringContextConstruction:
    """ScoringContext can be constructed with required and optional fields."""

    def test_minimal_construction(self) -> None:
        """ScoringContext can be built with just required fields."""
        ctx = ScoringContext(
            user_zip="36101",
            transit_dependent=False,
            schedule_type=AvailableHours.FLEXIBLE,
            barriers=[],
        )
        assert ctx.user_zip == "36101"
        assert ctx.transit_dependent is False
        assert ctx.schedule_type == AvailableHours.FLEXIBLE
        assert ctx.barriers == []
        assert ctx.benefits_profile is None

    def test_with_benefits_profile(self) -> None:
        """ScoringContext accepts an optional BenefitsProfile."""
        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=800,
            enrolled_programs=["SNAP"],
            dependents_under_6=1,
            dependents_6_to_17=0,
        )
        ctx = ScoringContext(
            user_zip="36104",
            transit_dependent=True,
            schedule_type=AvailableHours.DAYTIME,
            barriers=[BarrierType.CHILDCARE, BarrierType.CREDIT],
            benefits_profile=profile,
        )
        assert ctx.transit_dependent is True
        assert ctx.benefits_profile is not None
        assert ctx.benefits_profile.household_size == 3
        assert len(ctx.barriers) == 2

    def test_is_pydantic_model(self) -> None:
        """ScoringContext should be a Pydantic BaseModel."""
        from pydantic import BaseModel

        assert issubclass(ScoringContext, BaseModel)


def _job(**overrides: object) -> dict:
    base = {
        "title": "Cashier",
        "company": "Store",
        "location": "Montgomery, AL 36101",
        "description": "",
        "url": "https://example.com",
        "source": "test",
        "credit_check": "unknown",
        "transit_accessible": True,
        "industry_match": False,
        "schedule_conflict": False,
        "credit_blocked": False,
    }
    base.update(overrides)
    return base


class TestComputePvsWithContext:
    """compute_pvs accepts ScoringContext instead of individual params."""

    def test_accepts_scoring_context(self) -> None:
        """compute_pvs should work with ctx parameter."""
        ctx = ScoringContext(
            user_zip="36101",
            transit_dependent=False,
            schedule_type=AvailableHours.FLEXIBLE,
            barriers=[],
        )
        job = _job(description="Pay: $15.00 per hour")
        score = compute_pvs(job, ctx=ctx)
        assert 0.0 < score <= 1.0

    def test_context_with_benefits_profile(self) -> None:
        """compute_pvs with ScoringContext containing benefits_profile."""
        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=800,
            enrolled_programs=["SNAP"],
            dependents_under_6=1,
            dependents_6_to_17=0,
        )
        ctx = ScoringContext(
            user_zip="36101",
            transit_dependent=False,
            schedule_type=AvailableHours.FLEXIBLE,
            barriers=[],
            benefits_profile=profile,
        )
        job = _job(description="Pay: $15.00 per hour")
        score = compute_pvs(job, ctx=ctx)
        assert 0.0 < score <= 1.0


class TestRankAllJobsWithContext:
    """rank_all_jobs accepts ScoringContext instead of individual params."""

    def test_accepts_scoring_context(self) -> None:
        """rank_all_jobs should work with ctx parameter."""
        ctx = ScoringContext(
            user_zip="36101",
            transit_dependent=False,
            schedule_type=AvailableHours.FLEXIBLE,
            barriers=[],
        )
        jobs = [_job(description="Pay: $15.00 per hour")]
        ranked = rank_all_jobs(jobs, ctx=ctx)
        assert len(ranked) == 1
        assert 0.0 < ranked[0].relevance_score <= 1.0
