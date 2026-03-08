"""Tests for database query layer."""

import pytest

from app.core.queries import (
    create_session,
    get_all_resources,
    get_all_transit_routes,
    get_all_transit_stops,
    get_all_employers,
    get_resource_by_id,
    get_resources_by_category,
    get_session_by_id,
    update_session_plan,
)
from app.core.queries_jobs import get_all_job_listings, get_job_listing_by_id
from app.core.queries_feedback import (
    session_exists,
    insert_resource_feedback,
    token_exists,
    has_visit_feedback,
    insert_visit_feedback,
)
from app.modules.feedback.types import ResourceFeedbackRequest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_async_session_factory


@pytest.fixture
async def db_session(test_engine):
    """Yield an async session from the test engine."""
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


class TestGetAllResources:
    @pytest.mark.anyio
    async def test_returns_seeded_resources(self, db_session):
        """Should return all seeded resources as dicts."""
        results = await get_all_resources(db_session)
        assert len(results) > 0
        assert isinstance(results[0], dict)

    @pytest.mark.anyio
    async def test_resource_has_required_keys(self, db_session):
        """Each resource dict should have id, name, category."""
        results = await get_all_resources(db_session)
        first = results[0]
        assert "id" in first
        assert "name" in first
        assert "category" in first


class TestGetResourceById:
    @pytest.mark.anyio
    async def test_returns_resource_for_valid_id(self, db_session):
        """Should return a dict for an existing resource id."""
        result = await get_resource_by_id(db_session, 1)
        assert result is not None
        assert result["id"] == 1

    @pytest.mark.anyio
    async def test_returns_none_for_invalid_id(self, db_session):
        """Should return None when resource doesn't exist."""
        result = await get_resource_by_id(db_session, 99999)
        assert result is None


class TestGetResourcesByCategory:
    @pytest.mark.anyio
    async def test_filters_by_category(self, db_session):
        """Should return only resources matching the category."""
        results = await get_resources_by_category(db_session, "career_center")
        assert len(results) > 0
        assert all(r["category"] == "career_center" for r in results)

    @pytest.mark.anyio
    async def test_returns_empty_for_unknown_category(self, db_session):
        """Should return empty list for nonexistent category."""
        results = await get_resources_by_category(db_session, "nonexistent_xyz")
        assert results == []


class TestGetAllTransitRoutes:
    @pytest.mark.anyio
    async def test_returns_seeded_routes(self, db_session):
        """Should return all seeded transit routes."""
        results = await get_all_transit_routes(db_session)
        assert len(results) > 0
        assert isinstance(results[0], dict)

    @pytest.mark.anyio
    async def test_route_has_required_keys(self, db_session):
        """Each route dict should have id, route_number, route_name."""
        results = await get_all_transit_routes(db_session)
        first = results[0]
        assert "id" in first
        assert "route_number" in first
        assert "route_name" in first


class TestGetAllTransitStops:
    @pytest.mark.anyio
    async def test_returns_seeded_stops(self, db_session):
        """Should return all seeded transit stops."""
        results = await get_all_transit_stops(db_session)
        assert len(results) > 0
        assert isinstance(results[0], dict)

    @pytest.mark.anyio
    async def test_stop_has_required_keys(self, db_session):
        """Each stop dict should have lat and lng (coordinate-only query)."""
        results = await get_all_transit_stops(db_session)
        first = results[0]
        assert "lat" in first
        assert "lng" in first

    @pytest.mark.anyio
    async def test_stops_have_valid_coordinates(self, db_session):
        """All returned stops should have non-null coordinates."""
        results = await get_all_transit_stops(db_session)
        for stop in results:
            assert stop["lat"] is not None
            assert stop["lng"] is not None


class TestGetAllEmployers:
    @pytest.mark.anyio
    async def test_returns_empty_when_no_employers(self, db_session):
        """Should return empty list when no employers seeded."""
        results = await get_all_employers(db_session)
        assert isinstance(results, list)

    @pytest.mark.anyio
    async def test_returns_inserted_employer(self, test_engine):
        """Should return employers after manual insert."""
        async with test_engine.begin() as conn:
            await conn.execute(
                text("INSERT INTO employers (name, industry) VALUES (:name, :industry)"),
                {"name": "ACME Corp", "industry": "healthcare"},
            )
        factory = get_async_session_factory()
        async with factory() as session:
            results = await get_all_employers(session)
            assert len(results) == 1
            assert results[0]["name"] == "ACME Corp"
            assert "id" in results[0]


class TestCreateSession:
    @pytest.mark.anyio
    async def test_creates_session_and_returns_id(self, db_session):
        """Should insert a session row and return its UUID."""
        session_data = {
            "barriers": '["credit","transportation"]',
            "credit_profile": None,
            "qualifications": None,
            "plan": None,
        }
        session_id = await create_session(db_session, session_data)
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID format

    @pytest.mark.anyio
    async def test_uses_caller_provided_session_id(self, db_session):
        """Should use the provided session_id instead of generating one."""
        session_data = {
            "barriers": '["credit"]',
            "credit_profile": None,
            "qualifications": None,
            "plan": None,
        }
        session_id = await create_session(db_session, session_data, session_id="custom-id-123")
        assert session_id == "custom-id-123"
        result = await get_session_by_id(db_session, session_id)
        assert result is not None
        assert result["id"] == "custom-id-123"

    @pytest.mark.anyio
    async def test_session_has_expiry(self, db_session):
        """Created session should have expires_at set."""
        session_data = {
            "barriers": '["credit"]',
            "credit_profile": None,
            "qualifications": None,
            "plan": None,
        }
        session_id = await create_session(db_session, session_data)
        result = await get_session_by_id(db_session, session_id)
        assert result is not None
        assert result["expires_at"] is not None


class TestGetSessionById:
    @pytest.mark.anyio
    async def test_returns_session_for_valid_id(self, db_session):
        """Should return session dict for existing id."""
        session_data = {
            "barriers": '["housing"]',
            "credit_profile": None,
            "qualifications": None,
            "plan": None,
        }
        session_id = await create_session(db_session, session_data)
        result = await get_session_by_id(db_session, session_id)
        assert result is not None
        assert result["id"] == session_id
        assert result["barriers"] == '["housing"]'

    @pytest.mark.anyio
    async def test_returns_none_for_invalid_id(self, db_session):
        """Should return None for nonexistent session."""
        result = await get_session_by_id(db_session, "nonexistent-uuid")
        assert result is None

    @pytest.mark.anyio
    async def test_returns_none_for_expired_session(self, db_session):
        """Should return None when session has expired."""
        session_data = {
            "barriers": '["credit"]',
            "credit_profile": None,
            "qualifications": None,
            "plan": None,
        }
        session_id = await create_session(db_session, session_data)
        # Manually set expires_at to the past
        await db_session.execute(
            text("UPDATE sessions SET expires_at = '2020-01-01T00:00:00' WHERE id = :id"),
            {"id": session_id},
        )
        await db_session.commit()
        result = await get_session_by_id(db_session, session_id)
        assert result is None


class TestGetAllJobListings:
    @pytest.mark.anyio
    async def test_returns_seeded_listings(self, db_session):
        """Should return seed job listings from job_listings.json."""
        results = await get_all_job_listings(db_session)
        assert len(results) >= 25

    @pytest.mark.anyio
    async def test_returns_inserted_listing(self, test_engine):
        """Should return job listings after manual insert (on top of seeds)."""
        async with test_engine.begin() as conn:
            count_before = (await conn.execute(
                text("SELECT COUNT(*) FROM job_listings")
            )).scalar()
            await conn.execute(
                text(
                    "INSERT INTO job_listings (title, company, scraped_at) "
                    "VALUES (:title, :company, :scraped_at)"
                ),
                {"title": "CNA", "company": "Baptist", "scraped_at": "2026-03-01"},
            )
        factory = get_async_session_factory()
        async with factory() as session:
            results = await get_all_job_listings(session)
            assert len(results) == count_before + 1


class TestGetJobListingById:
    @pytest.mark.anyio
    async def test_returns_listing_for_valid_id(self, test_engine):
        """Should return job listing dict for existing id."""
        async with test_engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO job_listings (id, title, company, scraped_at) "
                    "VALUES (:id, :title, :company, :scraped_at)"
                ),
                {"id": 42, "title": "Nurse", "company": "Hospital", "scraped_at": "2026-03-01"},
            )
        factory = get_async_session_factory()
        async with factory() as session:
            result = await get_job_listing_by_id(session, 42)
            assert result is not None
            assert result["title"] == "Nurse"

    @pytest.mark.anyio
    async def test_returns_none_for_invalid_id(self, db_session):
        """Should return None for nonexistent job listing."""
        result = await get_job_listing_by_id(db_session, 99999)
        assert result is None


class TestUpdateSessionPlan:
    @pytest.mark.anyio
    async def test_updates_plan_column(self, db_session):
        """Should update the plan column for an existing session."""
        session_data = {
            "barriers": '["credit"]',
            "credit_profile": None,
            "qualifications": None,
            "plan": None,
        }
        session_id = await create_session(db_session, session_data)
        await update_session_plan(db_session, session_id, '{"plan_id": "p1"}')
        result = await get_session_by_id(db_session, session_id)
        assert result["plan"] == '{"plan_id": "p1"}'


class TestQueriesFeedbackDirect:
    """Direct tests for queries_feedback functions to cover lines missed by ASGI transport."""

    @pytest.mark.anyio
    async def test_session_exists_true_and_false(self, test_engine):
        """session_exists returns True for live session, False for missing one."""
        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            # Insert a non-expired session
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('sess-exist-1', '2026-03-06', '[]', '2099-01-01')"
            ))
            await session.commit()

            assert await session_exists(session, "sess-exist-1") is True
            assert await session_exists(session, "nonexistent-id") is False

    @pytest.mark.anyio
    async def test_insert_resource_feedback_commits(self, test_engine):
        """insert_resource_feedback persists feedback row via commit."""
        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            # Seed the required session row
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('00000000-0000-4000-8000-000000000001', '2026-03-06', '[]', '2099-01-01')"
            ))
            await session.commit()

            feedback = ResourceFeedbackRequest(
                resource_id=1,
                session_id="00000000-0000-4000-8000-000000000001",
                helpful=True,
                token="tok-1",
            )
            await insert_resource_feedback(session, feedback)

            result = await session.execute(text(
                "SELECT helpful FROM resource_feedback "
                "WHERE resource_id = 1 AND session_id = '00000000-0000-4000-8000-000000000001'"
            ))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1  # True stored as 1

    @pytest.mark.anyio
    async def test_token_exists_true_and_false(self, test_engine):
        """token_exists returns True for known token, False for unknown."""
        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('sess-tok-1', '2026-03-06', '[]', '2099-01-01')"
            ))
            await session.execute(text(
                "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                "VALUES ('known-token', 'sess-tok-1', '2026-03-06T00:00:00', '2099-01-01T00:00:00')"
            ))
            await session.commit()

            assert await token_exists(session, "known-token") is True
            assert await token_exists(session, "unknown-token") is False

    @pytest.mark.anyio
    async def test_has_visit_feedback_true_and_false(self, test_engine):
        """has_visit_feedback returns False before insert, True after insert_visit_feedback."""
        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            await session.execute(text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES ('sess-visit-direct', '2026-03-06', '[]', '2099-01-01')"
            ))
            await session.commit()

            assert await has_visit_feedback(session, "sess-visit-direct") is False

            await insert_visit_feedback(
                session,
                session_id="sess-visit-direct",
                made_it_to_center=2,
                outcomes_json='["got_interview"]',
                plan_accuracy=3,
                free_text=None,
            )

            assert await has_visit_feedback(session, "sess-visit-direct") is True
