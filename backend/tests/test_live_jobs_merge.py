"""Tests for job matching integration in generate_plan."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.matching.engine import generate_plan
from app.modules.matching.types import (
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    MatchBucket,
    ReEntryPlan,
    ScoredJobMatch,
    UserProfile,
)


def _make_profile(**overrides) -> UserProfile:
    defaults = {
        "session_id": str(uuid.uuid4()),
        "zip_code": "36104",
        "employment_status": EmploymentStatus.UNEMPLOYED,
        "barrier_count": 2,
        "primary_barriers": [BarrierType.CREDIT, BarrierType.TRANSPORTATION],
        "barrier_severity": BarrierSeverity.MEDIUM,
        "needs_credit_assessment": True,
        "transit_dependent": True,
        "schedule_type": "daytime",
        "work_history": "Former CNA at Baptist Hospital",
        "target_industries": ["healthcare"],
    }
    defaults.update(overrides)
    return UserProfile(**defaults)


def _make_job_listing(**overrides) -> dict:
    defaults = {
        "id": 1,
        "title": "Warehouse Worker",
        "company": "FedEx",
        "location": "Montgomery, AL",
        "description": "Entry-level warehouse position",
        "url": "https://example.com/job1",
        "source": "seed",
        "scraped_at": "2026-03-05T00:00:00Z",
        "expires_at": None,
        "credit_check": "not_required",
    }
    defaults.update(overrides)
    return defaults


_QUERY_PATCH = "app.modules.matching.engine.query_resources_for_barriers"
_MATCH_PATCH = "app.modules.matching.engine.match_jobs"


class TestGeneratePlanWithMatchJobs:
    @pytest.mark.asyncio
    async def test_plan_populates_bucketed_matches(self):
        """generate_plan should populate strong_matches, possible_matches, eligible_after_repair."""
        profile = _make_profile()
        mock_session = AsyncMock()

        strong = [ScoredJobMatch(
            title="CNA", company="Baptist", relevance_score=0.8,
            match_reason="Matches your CNA experience", bucket=MatchBucket.STRONG,
        )]
        possible = [ScoredJobMatch(
            title="Cashier", company="Walmart", relevance_score=0.4,
            match_reason="Entry-level opportunity", bucket=MatchBucket.POSSIBLE,
        )]
        after = [ScoredJobMatch(
            title="Bank Teller", company="Regions", relevance_score=0.5,
            match_reason="Matches target industry", bucket=MatchBucket.AFTER_REPAIR,
        )]

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_MATCH_PATCH, new_callable=AsyncMock, return_value=(strong, possible, after)),
        ):
            plan = await generate_plan(profile, mock_session)

        assert len(plan.strong_matches) == 1
        assert plan.strong_matches[0].title == "CNA"
        assert len(plan.possible_matches) == 1
        assert len(plan.eligible_after_repair) == 1

    @pytest.mark.asyncio
    async def test_empty_job_listings_graceful(self):
        """Empty match results should produce empty buckets."""
        profile = _make_profile()
        mock_session = AsyncMock()

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_MATCH_PATCH, new_callable=AsyncMock, return_value=([], [], [])),
        ):
            plan = await generate_plan(profile, mock_session)

        assert isinstance(plan, ReEntryPlan)
        assert plan.strong_matches == []
        assert plan.possible_matches == []

    @pytest.mark.asyncio
    async def test_next_steps_reference_top_match(self):
        """_build_next_steps should mention top strong match when available."""
        profile = _make_profile(
            primary_barriers=[BarrierType.TRANSPORTATION],
            barrier_severity=BarrierSeverity.LOW,
        )
        mock_session = AsyncMock()

        strong = [ScoredJobMatch(
            title="CNA", company="Baptist Health", relevance_score=0.85,
            match_reason="Matches your CNA experience", bucket=MatchBucket.STRONG,
        )]

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_MATCH_PATCH, new_callable=AsyncMock, return_value=(strong, [], [])),
        ):
            plan = await generate_plan(profile, mock_session)

        steps_text = " ".join(plan.immediate_next_steps)
        assert "CNA" in steps_text or "Baptist" in steps_text or "position" in steps_text

    @pytest.mark.asyncio
    async def test_job_matches_backward_compatible(self):
        """plan.job_matches should still contain all matches (flat list)."""
        profile = _make_profile()
        mock_session = AsyncMock()

        strong = [ScoredJobMatch(title="CNA", relevance_score=0.8, bucket=MatchBucket.STRONG)]
        possible = [ScoredJobMatch(title="Cashier", relevance_score=0.4, bucket=MatchBucket.POSSIBLE)]

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_MATCH_PATCH, new_callable=AsyncMock, return_value=(strong, possible, [])),
        ):
            plan = await generate_plan(profile, mock_session)

        assert len(plan.job_matches) == 2
