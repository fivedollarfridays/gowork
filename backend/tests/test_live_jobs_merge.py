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
        """generate_plan should split PVS-ranked flat list into legacy buckets."""
        profile = _make_profile()
        mock_session = AsyncMock()

        ranked = [
            ScoredJobMatch(
                title="CNA", company="Baptist", relevance_score=0.8,
                match_reason="Matches your CNA experience",
            ),
            ScoredJobMatch(
                title="Bank Teller", company="Regions", relevance_score=0.5,
                match_reason="Matches target industry",
                credit_check_required="required",
            ),
            ScoredJobMatch(
                title="Cashier", company="Walmart", relevance_score=0.4,
                match_reason="Entry-level opportunity",
            ),
        ]

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_MATCH_PATCH, new_callable=AsyncMock, return_value=ranked),
        ):
            plan = await generate_plan(profile, mock_session)

        assert len(plan.strong_matches) == 2
        assert plan.strong_matches[0].title == "CNA"
        assert plan.possible_matches == []
        assert len(plan.eligible_after_repair) == 1

    @pytest.mark.asyncio
    async def test_empty_job_listings_graceful(self):
        """Empty match results should produce empty buckets."""
        profile = _make_profile()
        mock_session = AsyncMock()

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_MATCH_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            plan = await generate_plan(profile, mock_session)

        assert isinstance(plan, ReEntryPlan)
        assert plan.strong_matches == []
        assert plan.possible_matches == []

    @pytest.mark.asyncio
    async def test_job_matches_computed_from_buckets(self):
        """plan.job_matches is computed from strong + possible + after_repair."""
        profile = _make_profile()
        mock_session = AsyncMock()

        ranked = [
            ScoredJobMatch(title="CNA", relevance_score=0.8),
            ScoredJobMatch(title="Cashier", relevance_score=0.4),
            ScoredJobMatch(title="Banker", relevance_score=0.3, credit_check_required="required"),
        ]

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_MATCH_PATCH, new_callable=AsyncMock, return_value=ranked),
        ):
            plan = await generate_plan(profile, mock_session)

        assert len(plan.after_repair) == 1
        assert plan.after_repair[0].title == "Banker"
        assert len(plan.job_matches) == 3  # computed: strong + possible + after_repair
        titles = [j.title for j in plan.job_matches]
        assert "CNA" in titles
        assert "Cashier" in titles
        assert "Banker" in titles
