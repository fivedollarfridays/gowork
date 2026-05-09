"""Tests for BrightData route endpoints.

Auth gating (T26.4 migration)
-----------------------------
The routes under ``/api/brightdata/...`` were originally header-gated
via ``require_admin_key`` (``X-Admin-Key``). T26.4 migrated the gate to
:func:`app.core.auth_roles.require_role("admin")` — the same S22 cookie
session every other admin surface uses. The tests below seed an admin
account in the test DB, mint a signed ``gw_account`` cookie, and pass
it on every authenticated request. Two extra cycles (non-admin and
anonymous) assert the new 403 contract distinguished by the ``detail``
string (matches the cities_admin convention).
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_roles
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.integrations.brightdata.types import (
    BrightDataAPIError,
    CrawlProgress,
    CrawlResult,
    CrawlStatus,
)
from app.routes._auth_claim_helpers import (
    SESSION_COOKIE_NAME,
    build_account_cookie_value,
)

_CLIENT_PATCH = "app.routes.brightdata.BrightDataClient"
_SETTINGS_PATCH = "app.routes.brightdata.get_settings"
_STORE_PATCH = "app.routes.brightdata.store_crawl_results"
_PRECRAWL_PATCH = "app.routes.brightdata.precrawl_jobs"


# -------------------- Fixtures --------------------


@pytest.fixture
async def auth_engine(test_engine):
    """test_engine + accounts + roles DDL applied on top.

    Mirrors the pattern used by test_cities_admin.py / test_admin_feedback.py:
    the role-based gate needs the accounts + roles tables to resolve the
    signed ``gw_account`` cookie back to an account holding the ``admin``
    role.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
    return test_engine


@pytest.fixture
def session_factory(auth_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        auth_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def auth_client(auth_engine):
    """Async client bound to ``app.main.app`` against the test engine."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# -------------------- Helpers --------------------


def _mock_settings(api_key: str = "key-123", dataset_id: str = "ds-123"):
    s = AsyncMock()
    s.brightdata_api_key = api_key
    s.brightdata_dataset_id = dataset_id
    return s


def _mock_client(**method_overrides):
    """Create a mock BrightDataClient that supports async context manager."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    for name, value in method_overrides.items():
        setattr(client, name, value)
    return client


async def _seed_admin(
    session: AsyncSession, email: str
) -> tuple[int, str]:
    account_id = await queries_accounts.create_account(session, email=email)
    await queries_roles.grant_role(session, account_id, "admin")
    return account_id, build_account_cookie_value(account_id)


async def _seed_non_admin(
    session: AsyncSession, email: str
) -> tuple[int, str]:
    account_id = await queries_accounts.create_account(session, email=email)
    return account_id, build_account_cookie_value(account_id)


async def _admin_cookie(session_factory, email: str) -> dict[str, str]:
    async with session_factory() as session:
        _aid, cookie = await _seed_admin(session, email)
    return {SESSION_COOKIE_NAME: cookie}


# -------------------- Auth gating (T26.4) --------------------


class TestAuthGating:
    """The 3-cycle contract: anon → 403, non-admin → 403, admin → 200.

    The two 403s are distinguished by the ``detail`` string — same
    convention as test_cities_admin.py.
    """

    @pytest.mark.anyio
    async def test_anonymous_returns_403(self, auth_client):
        resp = await auth_client.post(
            "/api/brightdata/crawl",
            json={"urls": ["https://indeed.com/jobs"]},
        )
        assert resp.status_code == 403
        assert "Authentication required" in resp.json().get("detail", "")

    @pytest.mark.anyio
    async def test_non_admin_returns_403(self, auth_client, session_factory):
        async with session_factory() as session:
            _aid, cookie = await _seed_non_admin(session, "user@example.com")
        resp = await auth_client.post(
            "/api/brightdata/crawl",
            json={"urls": ["https://indeed.com/jobs"]},
            cookies={SESSION_COOKIE_NAME: cookie},
        )
        assert resp.status_code == 403
        assert "Insufficient permissions" in resp.json().get("detail", "")

    @pytest.mark.anyio
    async def test_admin_cookie_succeeds(self, auth_client, session_factory):
        cookies = await _admin_cookie(session_factory, "admin@example.com")
        mock_client = _mock_client(
            trigger_crawl=AsyncMock(return_value="snap-auth"),
        )
        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
        ):
            resp = await auth_client.post(
                "/api/brightdata/crawl",
                json={"urls": ["https://indeed.com/jobs"]},
                cookies=cookies,
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["snapshot_id"] == "snap-auth"


# -------------------- Trigger --------------------


class TestTriggerCrawl:
    @pytest.mark.anyio
    async def test_trigger_success(self, auth_client, session_factory):
        cookies = await _admin_cookie(session_factory, "trigger1@example.com")
        mock_client = _mock_client(
            trigger_crawl=AsyncMock(return_value="snap-abc"),
        )
        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
        ):
            resp = await auth_client.post(
                "/api/brightdata/crawl",
                json={"urls": ["https://indeed.com/jobs?l=Montgomery+AL"]},
                cookies=cookies,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["snapshot_id"] == "snap-abc"
        assert data["status"] == "starting"

    @pytest.mark.anyio
    async def test_trigger_no_api_key(self, auth_client, session_factory):
        cookies = await _admin_cookie(session_factory, "trigger2@example.com")
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(api_key="")):
            resp = await auth_client.post(
                "/api/brightdata/crawl",
                json={"urls": ["https://indeed.com/jobs"]},
                cookies=cookies,
            )
        assert resp.status_code == 503

    @pytest.mark.anyio
    async def test_trigger_empty_urls_rejected(
        self, auth_client, session_factory,
    ):
        cookies = await _admin_cookie(session_factory, "trigger3@example.com")
        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            resp = await auth_client.post(
                "/api/brightdata/crawl",
                json={"urls": []},
                cookies=cookies,
            )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_trigger_api_error(self, auth_client, session_factory):
        cookies = await _admin_cookie(session_factory, "trigger4@example.com")
        mock_client = _mock_client(
            trigger_crawl=AsyncMock(
                side_effect=BrightDataAPIError(429, "rate limited")
            ),
        )
        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
        ):
            resp = await auth_client.post(
                "/api/brightdata/crawl",
                json={"urls": ["https://indeed.com/jobs"]},
                cookies=cookies,
            )
        assert resp.status_code == 502


# -------------------- Status --------------------


class TestCrawlStatus:
    @pytest.mark.anyio
    async def test_status_running(self, auth_client, session_factory):
        cookies = await _admin_cookie(session_factory, "status1@example.com")
        mock_client = _mock_client(
            get_snapshot_status=AsyncMock(return_value=CrawlProgress(
                snapshot_id="snap-abc",
                status=CrawlStatus.RUNNING,
                progress_pct=0.5,
            )),
        )
        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
        ):
            resp = await auth_client.get(
                "/api/brightdata/status/snap-abc", cookies=cookies,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert data["progress_pct"] == 0.5

    @pytest.mark.anyio
    async def test_status_ready_caches_results(
        self, auth_client, session_factory,
    ):
        cookies = await _admin_cookie(session_factory, "status2@example.com")
        jobs = [{"title": "Warehouse Worker"}, {"title": "CNA"}]
        mock_client = _mock_client(
            get_snapshot_status=AsyncMock(
                return_value=CrawlResult(snapshot_id="snap-abc", jobs=jobs)
            ),
        )
        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
            patch(
                _STORE_PATCH, new_callable=AsyncMock, return_value=2,
            ) as mock_store,
        ):
            resp = await auth_client.get(
                "/api/brightdata/status/snap-abc", cookies=cookies,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["jobs_found"] == 2
        mock_store.assert_called_once()

    @pytest.mark.anyio
    async def test_status_no_api_key(self, auth_client, session_factory):
        cookies = await _admin_cookie(session_factory, "status3@example.com")
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(api_key="")):
            resp = await auth_client.get(
                "/api/brightdata/status/snap-abc", cookies=cookies,
            )
        assert resp.status_code == 503

    @pytest.mark.anyio
    async def test_status_api_error(self, auth_client, session_factory):
        cookies = await _admin_cookie(session_factory, "status4@example.com")
        mock_client = _mock_client(
            get_snapshot_status=AsyncMock(
                side_effect=BrightDataAPIError(404, "not found")
            ),
        )
        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(_CLIENT_PATCH, return_value=mock_client),
        ):
            resp = await auth_client.get(
                "/api/brightdata/status/snap-bad", cookies=cookies,
            )
        assert resp.status_code == 502


# --- SEC-016: Snapshot ID validation ---


class TestSnapshotIdValidation:
    @pytest.mark.anyio
    async def test_invalid_snapshot_id_returns_422(
        self, auth_client, session_factory,
    ):
        """Special characters in snapshot_id rejected."""
        cookies = await _admin_cookie(session_factory, "snapid@example.com")
        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            resp = await auth_client.get(
                "/api/brightdata/status/snap%3BDROP%20TABLE",
                cookies=cookies,
            )
        assert resp.status_code == 422


# -------------------- Precrawl --------------------


class TestPrecrawl:
    @pytest.mark.anyio
    async def test_precrawl_success(self, auth_client, session_factory):
        cookies = await _admin_cookie(session_factory, "precrawl1@example.com")
        with (
            patch(_SETTINGS_PATCH, return_value=_mock_settings()),
            patch(
                _PRECRAWL_PATCH,
                new_callable=AsyncMock,
                return_value={
                    "snapshot_id": "snap-pre",
                    "jobs_cached": 15,
                    "skipped": False,
                },
            ),
        ):
            resp = await auth_client.post(
                "/api/brightdata/precrawl", cookies=cookies,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["jobs_cached"] == 15

    @pytest.mark.anyio
    async def test_precrawl_no_api_key(self, auth_client, session_factory):
        cookies = await _admin_cookie(session_factory, "precrawl2@example.com")
        with patch(_SETTINGS_PATCH, return_value=_mock_settings(api_key="")):
            resp = await auth_client.post(
                "/api/brightdata/precrawl", cookies=cookies,
            )
        assert resp.status_code == 503
