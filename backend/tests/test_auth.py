"""Tests for admin authentication dependency.

The ``require_admin_key`` header gate was previously exercised through
the BrightData routes; T26.4 migrated those routes to
``require_role("admin")`` (cookie session). The dependency itself is
still used by ``admin_flags`` / ``engagement.send-now`` / ``demo.seed``,
so we test it directly as a unit here rather than through a route.
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException


_SETTINGS_PATCH = "app.core.auth.get_settings"


def _mock_settings(admin_api_key: str = "test-admin-key-123"):
    from unittest.mock import MagicMock

    s = MagicMock()
    s.admin_api_key = admin_api_key
    return s


class TestRequireAdminKey:
    """Unit-test the ``require_admin_key`` dependency directly.

    Calling the async callable bypasses FastAPI's request lifecycle —
    that's intentional. The 422-on-missing-header behaviour is
    FastAPI's own ``Header(...)`` enforcement, not anything inside
    ``require_admin_key``; it's covered by routes that still use the
    dependency (e.g. test_admin_flags.py).
    """

    @pytest.mark.asyncio
    async def test_valid_key_passes(self):
        from app.core.auth import require_admin_key

        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            # Returning normally (no exception) means the gate passed.
            await require_admin_key(x_admin_key="test-admin-key-123")

    @pytest.mark.asyncio
    async def test_wrong_key_returns_403(self):
        from app.core.auth import require_admin_key

        with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
            with pytest.raises(HTTPException) as exc_info:
                await require_admin_key(x_admin_key="wrong-key")
        assert exc_info.value.status_code == 403
        assert "Invalid admin key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_empty_config_returns_503(self):
        from app.core.auth import require_admin_key

        with patch(_SETTINGS_PATCH, return_value=_mock_settings(admin_api_key="")):
            with pytest.raises(HTTPException) as exc_info:
                await require_admin_key(x_admin_key="any-key")
        assert exc_info.value.status_code == 503
        assert "not configured" in exc_info.value.detail


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
