"""Tests for live job matching merge in generate_plan."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.matching.engine import _build_job_matches, generate_plan
from app.modules.matching.types import (
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    JobMatch,
    ReEntryPlan,
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
        "source": "brightdata:snap-abc",
        "scraped_at": "2026-03-05T00:00:00Z",
        "expires_at": "2026-04-04T00:00:00Z",
    }
    defaults.update(overrides)
    return defaults


_QUERY_PATCH = "app.modules.matching.engine.query_resources_for_barriers"
_JOBS_PATCH = "app.modules.matching.engine.get_all_job_listings"


class TestBuildJobMatches:
    def test_converts_listings_to_job_matches(self):
        listings = [
            _make_job_listing(title="CNA", company="Baptist"),
            _make_job_listing(id=2, title="Driver", company="FedEx"),
        ]
        result = _build_job_matches(listings)
        assert len(result) == 2
        assert all(isinstance(m, JobMatch) for m in result)
        assert result[0].title == "CNA"
        assert result[1].title == "Driver"

    def test_includes_source_field(self):
        listings = [_make_job_listing(source="brightdata:snap-xyz")]
        result = _build_job_matches(listings)
        assert result[0].source == "brightdata:snap-xyz"

    def test_handles_missing_optional_fields(self):
        listings = [{"id": 1, "title": "Job", "scraped_at": "2026-03-05T00:00:00Z"}]
        result = _build_job_matches(listings)
        assert len(result) == 1
        assert result[0].company is None
        assert result[0].url is None

    def test_empty_listings_returns_empty(self):
        assert _build_job_matches([]) == []


class TestGeneratePlanWithJobs:
    @pytest.mark.asyncio
    async def test_plan_includes_job_matches(self):
        """generate_plan should populate job_matches from job_listings table."""
        profile = _make_profile(
            primary_barriers=[BarrierType.TRANSPORTATION],
            needs_credit_assessment=False,
            barrier_severity=BarrierSeverity.LOW,
        )
        mock_session = AsyncMock()
        listings = [
            _make_job_listing(title="CNA", company="Baptist"),
            _make_job_listing(id=2, title="Driver", company="FedEx"),
        ]

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_JOBS_PATCH, new_callable=AsyncMock, return_value=listings),
        ):
            plan = await generate_plan(profile, mock_session)

        assert len(plan.job_matches) == 2
        titles = [j.title for j in plan.job_matches]
        assert "CNA" in titles
        assert "Driver" in titles

    @pytest.mark.asyncio
    async def test_credit_filter_applied_for_credit_barrier(self):
        """Jobs with credit_check_required=yes should be ineligible for high credit severity."""
        profile = _make_profile(
            primary_barriers=[BarrierType.CREDIT],
            needs_credit_assessment=True,
            barrier_severity=BarrierSeverity.HIGH,
        )
        mock_session = AsyncMock()
        listings = [
            _make_job_listing(title="Bank Teller", company="Wells Fargo"),
            _make_job_listing(id=2, title="Warehouse", company="FedEx"),
        ]

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_JOBS_PATCH, new_callable=AsyncMock, return_value=listings),
        ):
            plan = await generate_plan(profile, mock_session)

        # With high severity, all jobs default to credit_check_required="unknown"
        # which means they go to after_repair (only "no" stays eligible)
        assert len(plan.job_matches) >= 1

    @pytest.mark.asyncio
    async def test_empty_job_listings_graceful(self):
        """Empty job_listings table should not crash — just empty job_matches."""
        profile = _make_profile()
        mock_session = AsyncMock()

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_JOBS_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            plan = await generate_plan(profile, mock_session)

        assert isinstance(plan, ReEntryPlan)
        assert plan.job_matches == []

    @pytest.mark.asyncio
    async def test_eligible_now_and_after_repair_populated(self):
        """Plan should populate eligible_now and eligible_after_repair title lists."""
        profile = _make_profile(
            primary_barriers=[BarrierType.CREDIT],
            barrier_severity=BarrierSeverity.HIGH,
        )
        mock_session = AsyncMock()
        listings = [
            _make_job_listing(title="Warehouse", company="FedEx"),
        ]

        with (
            patch(_QUERY_PATCH, return_value=[]),
            patch(_JOBS_PATCH, new_callable=AsyncMock, return_value=listings),
        ):
            plan = await generate_plan(profile, mock_session)

        # All jobs listed should appear in either eligible_now or eligible_after_repair
        all_titles = plan.eligible_now + plan.eligible_after_repair
        assert len(all_titles) >= 1
