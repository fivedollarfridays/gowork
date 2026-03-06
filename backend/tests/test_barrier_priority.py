"""Tests for barrier priority ordering."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.matching.barrier_priority import BARRIER_PRIORITY, prioritize_barriers
from app.modules.matching.types import (
    BarrierSeverity,
    BarrierType,
    EmploymentStatus,
    Resource,
    UserProfile,
)

_QUERY_PATCH = "app.modules.matching.engine.query_resources_for_barriers"


class TestBarrierPriority:
    def test_single_barrier(self):
        result = prioritize_barriers(["credit"])
        assert result == ["credit"]

    def test_all_barriers_sorted(self):
        all_barriers = list(BARRIER_PRIORITY.keys())
        result = prioritize_barriers(all_barriers)
        assert result == [
            "childcare", "transportation", "housing",
            "health", "credit", "criminal_record", "training",
        ]

    def test_unknown_barrier_appended_last(self):
        result = prioritize_barriers(["credit", "unknown_barrier"])
        assert result == ["credit", "unknown_barrier"]

    def test_empty_list(self):
        result = prioritize_barriers([])
        assert result == []

    def test_childcare_transportation_credit_order(self):
        """Childcare first, transportation second, credit third."""
        result = prioritize_barriers(["credit", "transportation", "childcare"])
        assert result == ["childcare", "transportation", "credit"]

    def test_priority_values_are_unique(self):
        values = list(BARRIER_PRIORITY.values())
        assert len(values) == len(set(values))

    def test_all_barrier_types_in_map(self):
        for bt in BarrierType:
            assert bt.value in BARRIER_PRIORITY


class TestBarrierPriorityInPlan:
    """Integration: barrier cards ordered by priority in plan output."""

    def _make_profile(self, **overrides) -> UserProfile:
        defaults = {
            "session_id": str(uuid.uuid4()),
            "zip_code": "36104",
            "employment_status": EmploymentStatus.UNEMPLOYED,
            "barrier_count": 3,
            "primary_barriers": [
                BarrierType.CREDIT,
                BarrierType.TRANSPORTATION,
                BarrierType.CHILDCARE,
            ],
            "barrier_severity": BarrierSeverity.MEDIUM,
            "needs_credit_assessment": True,
            "transit_dependent": True,
            "schedule_type": "daytime",
            "work_history": "Former CNA",
            "target_industries": ["healthcare"],
        }
        defaults.update(overrides)
        return UserProfile(**defaults)

    @pytest.mark.asyncio
    async def test_maria_barrier_card_order(self):
        """Maria: credit + transportation + childcare → childcare first."""
        from app.modules.matching.engine import generate_plan

        profile = self._make_profile(
            primary_barriers=[
                BarrierType.CREDIT,
                BarrierType.TRANSPORTATION,
                BarrierType.CHILDCARE,
            ],
        )
        mock_session = AsyncMock()

        with patch(_QUERY_PATCH, return_value=[]):
            plan = await generate_plan(profile, mock_session)

        card_types = [c.type for c in plan.barriers]
        assert card_types == [
            BarrierType.CHILDCARE,
            BarrierType.TRANSPORTATION,
            BarrierType.CREDIT,
        ]

    @pytest.mark.asyncio
    async def test_next_steps_follow_priority_order(self):
        """immediate_next_steps should follow priority ordering."""
        from app.modules.matching.engine import generate_plan

        profile = self._make_profile(
            primary_barriers=[
                BarrierType.CREDIT,
                BarrierType.TRANSPORTATION,
                BarrierType.CHILDCARE,
            ],
        )
        mock_session = AsyncMock()

        resources = [
            Resource(id=1, name="Credit Service", category="social_service"),
            Resource(id=2, name="MATS Transit", category="career_center"),
            Resource(id=3, name="DHR Childcare", category="childcare"),
        ]

        with patch(_QUERY_PATCH, return_value=resources):
            plan = await generate_plan(profile, mock_session)

        # First step is always Career Center
        assert "Career Center" in plan.immediate_next_steps[0]
        # Then barrier-specific steps in priority order (childcare, transportation, credit)
        barrier_steps = plan.immediate_next_steps[1:]
        assert any("DHR" in s for s in barrier_steps[:1])
