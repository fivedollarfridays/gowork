"""Tests for admin authentication dependency."""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient


_SETTINGS_PATCH = "app.core.auth.get_settings"


def _mock_settings(admin_api_key: str = "test-admin-key-123"):
    from unittest.mock import MagicMock

    s = MagicMock()
    s.admin_api_key = admin_api_key
    return s


class TestRequireAdminKey:
    """Test the require_admin_key FastAPI dependency via BrightData routes."""

    @pytest.mark.asyncio
    async def test_valid_key_passes(self):
        from app.main import app

        bd_settings = _mock_settings()
        bd_settings.brightdata_api_key = "key-123"
        bd_settings.brightdata_dataset_id = "ds-123"

        with (
            patch(_SETTINGS_PATCH, return_value=bd_settings),
            patch("app.routes.brightdata.get_settings", return_value=bd_settings),
            patch(
                "app.routes.brightdata.precrawl_montgomery_jobs",
                return_value={"snapshot_id": "snap-1", "jobs_cached": 5, "skipped": False},
            ),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post(
                    "/api/brightdata/precrawl",
                    headers={"X-Admin-Key": "test-admin-key-123"},
                )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_header_returns_422(self):
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/brightdata/precrawl")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_wrong_key_returns_403(self):
        from app.main import app

        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post(
                    "/api/brightdata/precrawl",
                    headers={"X-Admin-Key": "wrong-key"},
                )
        assert resp.status_code == 403
        assert "Invalid admin key" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_empty_config_returns_503(self):
        from app.main import app

        with patch(_SETTINGS_PATCH, return_value=_mock_settings(admin_api_key="")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post(
                    "/api/brightdata/precrawl",
                    headers={"X-Admin-Key": "any-key"},
                )
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"]


@pytest.mark.anyio
async def test_require_session_token_expired_raises_401():
    """When validate_token returns None but token_exists returns True, raise 401 expired."""
    from unittest.mock import AsyncMock, patch as mock_patch
    from fastapi import HTTPException
    from app.core.auth import require_session_token

    mock_db = AsyncMock()
    with mock_patch("app.core.auth.validate_token", new_callable=AsyncMock, return_value=None), \
         mock_patch("app.core.auth.token_exists", new_callable=AsyncMock, return_value=True):
        with pytest.raises(HTTPException) as exc_info:
            await require_session_token(mock_db, "sess-1", "expired-token")
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
