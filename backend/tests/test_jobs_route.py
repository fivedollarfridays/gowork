"""Tests for jobs route endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


_AGG_SEARCH_PATCH = "app.integrations.job_aggregator.JobAggregator.search"
_JOB_PATCH = "app.routes.jobs.get_job_listing_by_id"
_EMPLOYERS_PATCH = "app.routes.jobs.get_all_employers"
_TRANSIT_PATCH = "app.routes.jobs.get_all_transit_routes"


def _sample_jobs():
    return [
        {
            "id": 1, "title": "CNA", "company": "Baptist Hospital",
            "location": "Montgomery, AL", "description": "Certified nursing assistant",
            "url": "https://example.com/cna", "source": "seed",
            "scraped_at": "2026-03-01", "expires_at": None,
        },
        {
            "id": 2, "title": "Warehouse Associate", "company": "Amazon",
            "location": "Montgomery, AL", "description": "Warehouse work, no credit check",
            "url": "https://example.com/warehouse", "source": "seed",
            "scraped_at": "2026-03-01", "expires_at": None,
        },
        {
            "id": 3, "title": "Bank Teller", "company": "Regions Bank",
            "location": "Montgomery, AL", "description": "Customer service, credit check required",
            "url": "https://example.com/teller", "source": "seed",
            "scraped_at": "2026-03-01", "expires_at": None,
        },
    ]


def _sample_employers():
    return [
        {"id": 1, "name": "Baptist Hospital", "address": "301 Brown Springs Rd",
         "lat": 32.36, "lng": -86.27, "license_type": None, "industry": "healthcare", "active": 1},
        {"id": 2, "name": "Amazon", "address": "5501 Highway 80",
         "lat": 32.38, "lng": -86.35, "license_type": None, "industry": "logistics", "active": 1},
        {"id": 3, "name": "Regions Bank", "address": "60 Commerce St",
         "lat": 32.37, "lng": -86.30, "license_type": "banking", "industry": "finance", "active": 1},
    ]


def _sample_transit():
    return [
        {"id": 1, "route_number": 7, "route_name": "Troy Highway",
         "weekday_start": "05:00", "weekday_end": "21:00", "saturday": 1, "sunday": 0},
    ]


class TestGetJobs:
    @pytest.mark.asyncio
    async def test_returns_all_jobs(self):
        """GET /api/jobs returns all job listings."""
        from app.main import app

        with (
            patch(_AGG_SEARCH_PATCH, new_callable=AsyncMock, return_value=_sample_jobs()),
            patch(_EMPLOYERS_PATCH, new_callable=AsyncMock, return_value=_sample_employers()),
            patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=_sample_transit()),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/jobs/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["jobs"]) == 3

    @pytest.mark.asyncio
    async def test_filter_by_industry(self):
        """Industry filter narrows results."""
        from app.main import app

        with (
            patch(_AGG_SEARCH_PATCH, new_callable=AsyncMock, return_value=_sample_jobs()),
            patch(_EMPLOYERS_PATCH, new_callable=AsyncMock, return_value=_sample_employers()),
            patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=_sample_transit()),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/jobs/?industry=healthcare")
        assert resp.status_code == 200
        data = resp.json()
        assert all(j["industry"] == "healthcare" for j in data["jobs"])

    @pytest.mark.asyncio
    async def test_filter_transit_accessible(self):
        """Transit filter excludes non-accessible jobs."""
        from app.main import app

        with (
            patch(_AGG_SEARCH_PATCH, new_callable=AsyncMock, return_value=_sample_jobs()),
            patch(_EMPLOYERS_PATCH, new_callable=AsyncMock, return_value=_sample_employers()),
            patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=_sample_transit()),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/jobs/?transit_accessible=true")
        assert resp.status_code == 200
        data = resp.json()
        assert all(j.get("transit_info") is not None for j in data["jobs"])

    @pytest.mark.asyncio
    async def test_barrier_filter_credit(self):
        """Credit barrier filter excludes jobs requiring credit checks."""
        from app.main import app

        with (
            patch(_AGG_SEARCH_PATCH, new_callable=AsyncMock, return_value=_sample_jobs()),
            patch(_EMPLOYERS_PATCH, new_callable=AsyncMock, return_value=_sample_employers()),
            patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=_sample_transit()),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/jobs/?barriers=credit")
        assert resp.status_code == 200
        data = resp.json()
        for job in data["jobs"]:
            assert job.get("credit_check_required") != "yes"

    @pytest.mark.asyncio
    async def test_empty_results(self):
        """Returns empty list when no jobs match."""
        from app.main import app

        with (
            patch(_AGG_SEARCH_PATCH, new_callable=AsyncMock, return_value=[]),
            patch(_EMPLOYERS_PATCH, new_callable=AsyncMock, return_value=[]),
            patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/jobs/")
        assert resp.status_code == 200
        assert resp.json()["jobs"] == []


class TestGetJobById:
    @pytest.mark.asyncio
    async def test_returns_single_job(self):
        """GET /api/jobs/{id} returns job with details."""
        from app.main import app

        job = _sample_jobs()[0]
        with (
            patch(_JOB_PATCH, new_callable=AsyncMock, return_value=job),
            patch(_EMPLOYERS_PATCH, new_callable=AsyncMock, return_value=_sample_employers()),
            patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=_sample_transit()),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/jobs/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "CNA"
        assert "application_steps" in data

    @pytest.mark.asyncio
    async def test_404_for_missing_job(self):
        """Returns 404 when job not found."""
        from app.main import app

        with (
            patch(_JOB_PATCH, new_callable=AsyncMock, return_value=None),
            patch(_EMPLOYERS_PATCH, new_callable=AsyncMock, return_value=[]),
            patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/jobs/999")
        assert resp.status_code == 404


class TestTransitSchedule:
    def test_weekday_hours(self):
        """Transit schedule respects M-Transit weekday hours."""
        from app.routes.jobs import is_transit_accessible

        route = {"weekday_start": "05:00", "weekday_end": "21:00", "saturday": 1, "sunday": 0}
        assert is_transit_accessible(route, "daytime") is True
        assert is_transit_accessible(route, "evening") is True
        assert is_transit_accessible(route, "night") is False

    def test_no_sunday_service(self):
        """M-Transit has no Sunday service."""
        from app.routes.jobs import is_transit_accessible

        route = {"weekday_start": "05:00", "weekday_end": "21:00", "saturday": 1, "sunday": 0}
        assert is_transit_accessible(route, "daytime") is True

    def test_missing_weekday_end_returns_accessible(self):
        """Route with missing weekday_end defaults to accessible."""
        from app.routes.jobs import is_transit_accessible

        assert is_transit_accessible({}, "night") is True
        assert is_transit_accessible({"weekday_end": ""}, "night") is True


class TestJobsRateLimit:
    """Rate limiting on jobs endpoints (MED-3)."""

    @pytest.mark.asyncio
    async def test_list_jobs_rate_limited(self):
        """GET /api/jobs/ returns 429 after exceeding rate limit."""
        from app.main import app
        from app.routes.jobs import _list_rate_limiter

        _list_rate_limiter.clear()

        with (
            patch(_AGG_SEARCH_PATCH, new_callable=AsyncMock, return_value=[]),
            patch(_EMPLOYERS_PATCH, new_callable=AsyncMock, return_value=[]),
            patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=[]),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Send 60 requests (the limit)
                for _ in range(60):
                    await client.get("/api/jobs/")
                # 61st should be blocked
                resp = await client.get("/api/jobs/")
        assert resp.status_code == 429
        _list_rate_limiter.clear()

    @pytest.mark.asyncio
    async def test_get_job_rate_limited(self):
        """GET /api/jobs/{id} returns 429 after exceeding rate limit."""
        from app.main import app
        from app.routes.jobs import _detail_rate_limiter

        _detail_rate_limiter.clear()

        job = _sample_jobs()[0]
        with (
            patch(_JOB_PATCH, new_callable=AsyncMock, return_value=job),
            patch(_EMPLOYERS_PATCH, new_callable=AsyncMock, return_value=_sample_employers()),
            patch(_TRANSIT_PATCH, new_callable=AsyncMock, return_value=_sample_transit()),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Send 120 requests (the limit)
                for _ in range(120):
                    await client.get("/api/jobs/1")
                # 121st should be blocked
                resp = await client.get("/api/jobs/1")
        assert resp.status_code == 429
        _detail_rate_limiter.clear()


class TestCreditBarrierFilter:
    def test_filters_credit_check_jobs(self):
        """Jobs with license_type=banking are credit-check-required."""
        from app.routes.jobs import requires_credit_check

        assert requires_credit_check("banking") is True
        assert requires_credit_check("finance") is True
        assert requires_credit_check(None) is False
        assert requires_credit_check("healthcare") is False
