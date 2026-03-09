"""Tests for criminal record profile — T26.1.

Tests cover:
- RecordProfile model validation + defaults
- RecordType / ChargeCategory enums
- DB round-trip (insert + get)
- record_profiles table exists
- Assessment stores record profile when provided
- Assessment works without record profile (backward compat)
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.modules.criminal.record_profile import (
    ChargeCategory,
    RecordProfile,
    RecordType,
)
from app.modules.matching.types import BarrierType, ReEntryPlan, UserProfile


# ---------------------------------------------------------------------------
# Model validation tests
# ---------------------------------------------------------------------------

class TestRecordProfileModel:
    def test_default_empty_profile(self):
        """Empty profile should have safe defaults."""
        profile = RecordProfile()
        assert profile.record_types == []
        assert profile.charge_categories == []
        assert profile.years_since_conviction is None
        assert profile.completed_sentence is False

    def test_full_profile(self):
        """All fields populated."""
        profile = RecordProfile(
            record_types=[RecordType.FELONY, RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT, ChargeCategory.DRUG],
            years_since_conviction=5,
            completed_sentence=True,
        )
        assert RecordType.FELONY in profile.record_types
        assert ChargeCategory.DRUG in profile.charge_categories
        assert profile.years_since_conviction == 5
        assert profile.completed_sentence is True

    def test_serialization_round_trip(self):
        """Model -> JSON -> Model round-trip."""
        original = RecordProfile(
            record_types=[RecordType.ARREST_ONLY],
            charge_categories=[ChargeCategory.OTHER],
            years_since_conviction=2,
            completed_sentence=False,
        )
        data = json.loads(original.model_dump_json())
        restored = RecordProfile(**data)
        assert restored == original


class TestRecordTypeEnum:
    def test_all_values(self):
        assert RecordType.FELONY == "felony"
        assert RecordType.MISDEMEANOR == "misdemeanor"
        assert RecordType.ARREST_ONLY == "arrest_only"
        assert RecordType.EXPUNGED == "expunged"

    def test_from_string(self):
        assert RecordType("felony") == RecordType.FELONY


class TestChargeCategoryEnum:
    def test_all_values(self):
        assert ChargeCategory.VIOLENCE == "violence"
        assert ChargeCategory.THEFT == "theft"
        assert ChargeCategory.DRUG == "drug"
        assert ChargeCategory.DUI == "dui"
        assert ChargeCategory.SEX_OFFENSE == "sex_offense"
        assert ChargeCategory.FRAUD == "fraud"
        assert ChargeCategory.OTHER == "other"


# ---------------------------------------------------------------------------
# UserProfile integration
# ---------------------------------------------------------------------------

class TestUserProfileRecordField:
    def test_record_profile_defaults_none(self):
        """UserProfile.record_profile should default to None."""
        profile = UserProfile(
            session_id="s1",
            zip_code="36104",
            employment_status="unemployed",
            barrier_count=1,
            primary_barriers=[BarrierType.CRIMINAL_RECORD],
            barrier_severity="low",
            needs_credit_assessment=False,
            transit_dependent=False,
            schedule_type="daytime",
            work_history="test",
            target_industries=[],
        )
        assert profile.record_profile is None

    def test_record_profile_attached(self):
        """UserProfile should accept a RecordProfile."""
        rp = RecordProfile(record_types=[RecordType.MISDEMEANOR])
        profile = UserProfile(
            session_id="s1",
            zip_code="36104",
            employment_status="unemployed",
            barrier_count=1,
            primary_barriers=[BarrierType.CRIMINAL_RECORD],
            barrier_severity="low",
            needs_credit_assessment=False,
            transit_dependent=False,
            schedule_type="daytime",
            work_history="test",
            target_industries=[],
            record_profile=rp,
        )
        assert profile.record_profile is not None
        assert RecordType.MISDEMEANOR in profile.record_profile.record_types


# ---------------------------------------------------------------------------
# Database round-trip tests
# ---------------------------------------------------------------------------

class TestRecordProfileDB:
    @pytest.mark.anyio
    async def test_table_exists(self, test_engine):
        """record_profiles table should be created by DDL."""
        from sqlalchemy import text
        from app.core.database import get_async_session_factory

        factory = get_async_session_factory()
        async with factory() as session:
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='record_profiles'")
            )
            assert result.scalar() == "record_profiles"

    @pytest.mark.anyio
    async def test_insert_and_get(self, test_engine):
        """Insert and retrieve a record profile."""
        from app.core.database import get_async_session_factory
        from app.core.queries import insert_record_profile, get_record_profile

        factory = get_async_session_factory()
        async with factory() as session:
            rp = RecordProfile(
                record_types=[RecordType.FELONY],
                charge_categories=[ChargeCategory.THEFT],
                years_since_conviction=3,
                completed_sentence=True,
            )
            await insert_record_profile(session, "session-abc", rp)
            result = await get_record_profile(session, "session-abc")

        assert result is not None
        assert RecordType.FELONY in result.record_types
        assert ChargeCategory.THEFT in result.charge_categories
        assert result.years_since_conviction == 3
        assert result.completed_sentence is True

    @pytest.mark.anyio
    async def test_get_nonexistent_returns_none(self, test_engine):
        """Getting a non-existent profile returns None."""
        from app.core.database import get_async_session_factory
        from app.core.queries import get_record_profile

        factory = get_async_session_factory()
        async with factory() as session:
            result = await get_record_profile(session, "nonexistent")
        assert result is None

    @pytest.mark.anyio
    async def test_upsert_replaces(self, test_engine):
        """Second insert for same session_id should replace."""
        from app.core.database import get_async_session_factory
        from app.core.queries import insert_record_profile, get_record_profile

        factory = get_async_session_factory()
        async with factory() as session:
            rp1 = RecordProfile(record_types=[RecordType.FELONY])
            await insert_record_profile(session, "session-xyz", rp1)
            rp2 = RecordProfile(record_types=[RecordType.MISDEMEANOR])
            await insert_record_profile(session, "session-xyz", rp2)
            result = await get_record_profile(session, "session-xyz")

        assert result is not None
        assert RecordType.MISDEMEANOR in result.record_types
        assert RecordType.FELONY not in result.record_types


# ---------------------------------------------------------------------------
# Assessment endpoint integration
# ---------------------------------------------------------------------------

def _mock_plan() -> ReEntryPlan:
    return ReEntryPlan(
        plan_id="test-plan-id",
        session_id="test-session",
        barriers=[],
        immediate_next_steps=["Visit a career center"],
    )


_GEN_PATCH = "app.routes.assessment.generate_plan"
_SESSION_PATCH = "app.routes.assessment.create_session"
_UPDATE_PLAN_PATCH = "app.routes.assessment.update_session_plan"
_FEEDBACK_TOKEN_PATCH = "app.routes.assessment.create_feedback_token"
_RECORD_INSERT_PATCH = "app.routes.assessment.insert_record_profile"


class TestAssessmentWithRecordProfile:
    @pytest.fixture(autouse=True)
    def _clear_rate_limiter(self):
        from app.routes.assessment import _rate_limiter
        _rate_limiter.clear()

    @pytest.mark.asyncio
    async def test_record_profile_stored_when_provided(self):
        """Assessment with record_profile should call insert_record_profile."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, return_value="test-uuid"),
            patch(_UPDATE_PLAN_PATCH, new_callable=AsyncMock),
            patch(_FEEDBACK_TOKEN_PATCH, new_callable=AsyncMock, return_value="tk"),
            patch(_RECORD_INSERT_PATCH, new_callable=AsyncMock) as mock_insert,
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"criminal_record": True},
                    "work_history": "Former warehouse worker",
                    "record_profile": {
                        "record_types": ["misdemeanor"],
                        "charge_categories": ["theft"],
                        "years_since_conviction": 4,
                        "completed_sentence": True,
                    },
                })
        assert resp.status_code == 201
        mock_insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_record_profile_still_works(self):
        """Assessment without record_profile should work (backward compat)."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, return_value="test-uuid"),
            patch(_UPDATE_PLAN_PATCH, new_callable=AsyncMock),
            patch(_FEEDBACK_TOKEN_PATCH, new_callable=AsyncMock, return_value="tk"),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"criminal_record": True},
                    "work_history": "Former warehouse worker",
                })
        assert resp.status_code == 201
        data = resp.json()
        assert data["profile"]["record_profile"] is None

    @pytest.mark.asyncio
    async def test_record_profile_in_response(self):
        """Record profile should appear in profile response."""
        from app.main import app

        with (
            patch(_GEN_PATCH, return_value=_mock_plan()),
            patch(_SESSION_PATCH, return_value="test-uuid"),
            patch(_UPDATE_PLAN_PATCH, new_callable=AsyncMock),
            patch(_FEEDBACK_TOKEN_PATCH, new_callable=AsyncMock, return_value="tk"),
            patch(_RECORD_INSERT_PATCH, new_callable=AsyncMock),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/assessment/", json={
                    "zip_code": "36104",
                    "employment_status": "unemployed",
                    "barriers": {"criminal_record": True},
                    "work_history": "Former warehouse worker",
                    "record_profile": {
                        "record_types": ["felony"],
                        "charge_categories": ["drug"],
                        "years_since_conviction": 6,
                        "completed_sentence": True,
                    },
                })
        assert resp.status_code == 201
        data = resp.json()
        rp = data["profile"]["record_profile"]
        assert rp is not None
        assert "felony" in rp["record_types"]
        assert rp["years_since_conviction"] == 6
