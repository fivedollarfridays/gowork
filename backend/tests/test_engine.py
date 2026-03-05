"""Tests for matching engine orchestrator."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.matching.engine import generate_plan, query_resources_for_barriers
from app.modules.matching.types import (
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    ReEntryPlan,
    Resource,
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


def _make_resource_dict(**overrides) -> dict:
    defaults = {
        "id": 1,
        "name": "Career Center",
        "category": "career_center",
        "subcategory": None,
        "address": "123 Main St, Montgomery, AL 36104",
        "lat": None,
        "lng": None,
        "phone": "334-555-0100",
        "url": None,
        "eligibility": None,
        "services": None,
        "hours": None,
        "notes": None,
    }
    defaults.update(overrides)
    return defaults


def _make_resource(**overrides) -> Resource:
    defaults = {"id": 1, "name": "Career Center", "category": "career_center"}
    defaults.update(overrides)
    return Resource(**defaults)


_QUERY_PATCH = "app.modules.matching.engine.query_resources_for_barriers"
_CAT_PATCH = "app.modules.matching.engine.get_resources_by_category"


class TestQueryResourcesForBarriers:
    @pytest.mark.asyncio
    async def test_returns_resources_matching_barrier_categories(self):
        """Should fetch resources for categories matching user barriers."""
        career = _make_resource_dict(id=1, name="Career Center", category="career_center")
        childcare = _make_resource_dict(id=2, name="Daycare", category="childcare")
        training = _make_resource_dict(id=3, name="Training", category="training")

        mock_session = AsyncMock()

        async def mock_get_by_category(session, category):
            return [r for r in [career, childcare, training] if r["category"] == category]

        with patch(_CAT_PATCH, side_effect=mock_get_by_category):
            result = await query_resources_for_barriers(
                [BarrierType.CREDIT], mock_session
            )
        # CREDIT maps to career_center and social_service
        assert any(r.name == "Career Center" for r in result)

    @pytest.mark.asyncio
    async def test_deduplicates_resources(self):
        """Resources appearing in multiple categories should not be duplicated."""
        career = _make_resource_dict(id=1, name="Career Center", category="career_center")

        mock_session = AsyncMock()

        async def mock_get_by_category(session, category):
            if category == "career_center":
                return [career]
            return []

        with patch(_CAT_PATCH, side_effect=mock_get_by_category):
            # CREDIT and TRANSPORTATION both map to career_center
            result = await query_resources_for_barriers(
                [BarrierType.CREDIT, BarrierType.TRANSPORTATION], mock_session
            )
        ids = [r.id for r in result]
        assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_empty_barriers_returns_empty(self):
        """No barriers -> no resources."""
        mock_session = AsyncMock()
        result = await query_resources_for_barriers([], mock_session)
        assert result == []


class TestGeneratePlan:
    @pytest.mark.asyncio
    async def test_returns_reentry_plan(self):
        """Should return a complete ReEntryPlan."""
        profile = _make_profile()
        mock_session = AsyncMock()

        resources = [
            _make_resource(id=1, name="Career Center", category="career_center"),
            _make_resource(id=2, name="Social Service", category="social_service"),
        ]

        with patch(_QUERY_PATCH, return_value=resources):
            plan = await generate_plan(profile, mock_session)

        assert isinstance(plan, ReEntryPlan)
        assert plan.session_id == profile.session_id

    @pytest.mark.asyncio
    async def test_plan_has_barrier_cards(self):
        """Should create a BarrierCard for each primary barrier."""
        profile = _make_profile(
            primary_barriers=[BarrierType.CREDIT, BarrierType.TRANSPORTATION],
        )
        mock_session = AsyncMock()

        resources = [
            _make_resource(id=1, name="Career Center", category="career_center"),
        ]

        with patch(_QUERY_PATCH, return_value=resources):
            plan = await generate_plan(profile, mock_session)

        barrier_types = [b.type for b in plan.barriers]
        assert BarrierType.CREDIT in barrier_types
        assert BarrierType.TRANSPORTATION in barrier_types

    @pytest.mark.asyncio
    async def test_plan_has_immediate_next_steps(self):
        """Should populate immediate_next_steps."""
        profile = _make_profile()
        mock_session = AsyncMock()

        with patch(_QUERY_PATCH, return_value=[_make_resource()]):
            plan = await generate_plan(profile, mock_session)

        assert len(plan.immediate_next_steps) > 0

    @pytest.mark.asyncio
    async def test_plan_id_is_uuid(self):
        """Plan ID should be a valid UUID."""
        profile = _make_profile()
        mock_session = AsyncMock()

        with patch(_QUERY_PATCH, return_value=[]):
            plan = await generate_plan(profile, mock_session)

        uuid.UUID(plan.plan_id)  # raises if invalid

    @pytest.mark.asyncio
    async def test_barrier_cards_have_resources(self):
        """BarrierCards should include matched resources."""
        profile = _make_profile(primary_barriers=[BarrierType.CHILDCARE])
        mock_session = AsyncMock()

        childcare_resource = _make_resource(
            id=5, name="Daycare A", category="childcare",
            address="123 Main St, Montgomery, AL 36104",
        )

        with patch(_QUERY_PATCH, return_value=[childcare_resource]):
            plan = await generate_plan(profile, mock_session)

        childcare_cards = [b for b in plan.barriers if b.type == BarrierType.CHILDCARE]
        assert len(childcare_cards) == 1
        assert len(childcare_cards[0].resources) > 0

    @pytest.mark.asyncio
    async def test_barrier_cards_have_actions(self):
        """Each BarrierCard should have action steps."""
        profile = _make_profile(primary_barriers=[BarrierType.CREDIT])
        mock_session = AsyncMock()

        with patch(_QUERY_PATCH, return_value=[_make_resource()]):
            plan = await generate_plan(profile, mock_session)

        credit_cards = [b for b in plan.barriers if b.type == BarrierType.CREDIT]
        assert len(credit_cards) == 1
        assert len(credit_cards[0].actions) > 0

    @pytest.mark.asyncio
    async def test_certification_renewal_adds_to_plan(self):
        """Work history with CNA should add certification info."""
        profile = _make_profile(
            work_history="Former CNA at Baptist Hospital",
            primary_barriers=[BarrierType.TRAINING],
        )
        mock_session = AsyncMock()

        with patch(_QUERY_PATCH, return_value=[_make_resource(category="training")]):
            plan = await generate_plan(profile, mock_session)

        training_cards = [b for b in plan.barriers if b.type == BarrierType.TRAINING]
        assert len(training_cards) == 1
        actions_text = " ".join(training_cards[0].actions)
        assert "CNA" in actions_text

    @pytest.mark.asyncio
    async def test_no_barriers_produces_minimal_plan(self):
        """Profile with no barriers still returns valid plan."""
        profile = _make_profile(primary_barriers=[], barrier_count=0)
        mock_session = AsyncMock()

        with patch(_QUERY_PATCH, return_value=[]):
            plan = await generate_plan(profile, mock_session)

        assert isinstance(plan, ReEntryPlan)
        assert len(plan.barriers) == 0
