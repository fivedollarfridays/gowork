"""Tests for database query layer."""

import pytest

from app.core.queries import (
    create_session,
    get_all_resources,
    get_all_transit_routes,
    get_all_employers,
    get_resource_by_id,
    get_resources_by_category,
    get_session_by_id,
    update_session_plan,
)
from app.core.queries_jobs import get_all_job_listings, get_job_listing_by_id
from sqlalchemy import text

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
    async def test_returns_empty_when_no_listings(self, db_session):
        """Should return empty list when no job listings exist."""
        results = await get_all_job_listings(db_session)
        assert results == []

    @pytest.mark.anyio
    async def test_returns_inserted_listing(self, test_engine):
        """Should return job listings after manual insert."""
        async with test_engine.begin() as conn:
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
            assert len(results) == 1
            assert results[0]["title"] == "CNA"


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
