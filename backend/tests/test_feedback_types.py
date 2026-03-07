"""Tests for feedback module types and schema."""

import pytest
from pydantic import ValidationError

from app.modules.feedback.types import (
    ResourceFeedbackRequest,
    ResourceFeedbackResponse,
    ResourceHealth,
    VisitFeedbackRequest,
    VisitFeedbackResponse,
)


class TestResourceHealth:
    def test_enum_values(self):
        """ResourceHealth has HEALTHY, WATCH, FLAGGED, HIDDEN."""
        assert ResourceHealth.HEALTHY == "healthy"
        assert ResourceHealth.WATCH == "watch"
        assert ResourceHealth.FLAGGED == "flagged"
        assert ResourceHealth.HIDDEN == "hidden"

    def test_enum_is_str(self):
        """ResourceHealth values are strings for DB storage."""
        assert isinstance(ResourceHealth.HEALTHY, str)


class TestResourceFeedbackRequest:
    def test_valid_request(self):
        """Valid resource feedback request should parse."""
        req = ResourceFeedbackRequest(
            resource_id=1,
            session_id="00000000-0000-4000-8000-000000000001",
            helpful=True,
            barrier_type="credit",
            token="tok-t",
        )
        assert req.resource_id == 1
        assert req.helpful is True

    def test_missing_resource_id_fails(self):
        """resource_id is required."""
        with pytest.raises(ValidationError):
            ResourceFeedbackRequest(
                session_id="00000000-0000-4000-8000-000000000001", helpful=True, barrier_type="credit", token="t"
            )

    def test_missing_session_id_fails(self):
        """session_id is required."""
        with pytest.raises(ValidationError):
            ResourceFeedbackRequest(
                resource_id=1, helpful=True, barrier_type="credit", token="t"
            )

    def test_barrier_type_optional(self):
        """barrier_type can be None."""
        req = ResourceFeedbackRequest(
            resource_id=1, session_id="00000000-0000-4000-8000-000000000001", helpful=False, token="t"
        )
        assert req.barrier_type is None


class TestResourceFeedbackResponse:
    def test_success_response(self):
        """Response includes success, resource_id, helpful."""
        resp = ResourceFeedbackResponse(
            success=True, resource_id=1, helpful=True
        )
        assert resp.success is True
        assert resp.resource_id == 1


class TestVisitFeedbackRequest:
    def test_valid_full_request(self):
        """Full visit feedback request with all fields."""
        req = VisitFeedbackRequest(
            token="tok-123",
            made_it_to_center=1,
            outcomes=["wioa_approved", "training_referred"],
            plan_accuracy=1,
            free_text="Everything was great",
        )
        assert req.token == "tok-123"
        assert req.made_it_to_center == 1
        assert len(req.outcomes) == 2

    def test_made_it_to_center_range(self):
        """made_it_to_center must be 0, 1, or 2."""
        req = VisitFeedbackRequest(
            token="t", made_it_to_center=0, outcomes=[], plan_accuracy=1
        )
        assert req.made_it_to_center == 0

        req2 = VisitFeedbackRequest(
            token="t", made_it_to_center=2, outcomes=[], plan_accuracy=1
        )
        assert req2.made_it_to_center == 2

    def test_plan_accuracy_range(self):
        """plan_accuracy must be 1, 2, or 3."""
        req = VisitFeedbackRequest(
            token="t", made_it_to_center=1, outcomes=[], plan_accuracy=3
        )
        assert req.plan_accuracy == 3

    def test_free_text_optional(self):
        """free_text defaults to None."""
        req = VisitFeedbackRequest(
            token="t", made_it_to_center=1, outcomes=[], plan_accuracy=1
        )
        assert req.free_text is None

    def test_outcomes_default_empty(self):
        """outcomes defaults to empty list."""
        req = VisitFeedbackRequest(
            token="t", made_it_to_center=0, plan_accuracy=1
        )
        assert req.outcomes == []


class TestVisitFeedbackResponse:
    def test_success_response(self):
        """Response includes success flag."""
        resp = VisitFeedbackResponse(success=True)
        assert resp.success is True


class TestFeedbackTablesExist:
    @pytest.mark.anyio
    async def test_feedback_tokens_table(self, test_engine):
        """feedback_tokens table should exist after init."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_tokens'")
            )
            assert result.scalar() == "feedback_tokens"

    @pytest.mark.anyio
    async def test_visit_feedback_table(self, test_engine):
        """visit_feedback table should exist after init."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='visit_feedback'")
            )
            assert result.scalar() == "visit_feedback"

    @pytest.mark.anyio
    async def test_resource_feedback_table(self, test_engine):
        """resource_feedback table should exist after init."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='resource_feedback'")
            )
            assert result.scalar() == "resource_feedback"

    @pytest.mark.anyio
    async def test_resources_has_health_status(self, test_engine):
        """resources table should have health_status column."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            result = await session.execute(text("PRAGMA table_info(resources)"))
            columns = {row[1] for row in result.fetchall()}
            assert "health_status" in columns
