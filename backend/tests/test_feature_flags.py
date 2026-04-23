"""Tests for the feature-flag infrastructure (T12.0b).

Covers:
- is_enabled() resolution chain: env > yaml > default
- Truthy / falsy env-var parsing
- set_flag_runtime() audit writes (SHA256 hash, 7 fields)
- Rate limiter (10 toggles per actor_token_hash per hour)
- Admin endpoint: auth, audit write, 429 on rate-limit, AI warning log
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


_SETTINGS_PATCH = "app.core.auth.get_settings"
_ADMIN_KEY = "test-admin-key-123"


def _mock_settings():
    s = MagicMock()
    s.admin_api_key = _ADMIN_KEY
    return s


# -------------------- YAML / env resolution (pure unit) --------------------


@pytest.fixture
def tmp_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point feature_flags at a temp YAML file; return the path for writing."""
    import app.core.feature_flags as ff

    yaml_path = tmp_path / "flags.yaml"
    monkeypatch.setattr(ff, "_YAML_PATH", yaml_path)
    ff._reset_state_for_tests()
    return yaml_path


def _write_yaml(path: Path, contents: str) -> None:
    path.write_text(contents)


def test_is_enabled_env_precedence_over_yaml(
    tmp_yaml: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env var wins when both env and yaml set the same flag."""
    from app.core.feature_flags import is_enabled

    _write_yaml(tmp_yaml, "MY_FLAG: false\n")
    monkeypatch.setenv("FEATURE_MY_FLAG", "true")

    assert is_enabled("MY_FLAG") is True


def test_is_enabled_yaml_precedence_over_default(
    tmp_yaml: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """YAML wins over default when env var is unset."""
    from app.core.feature_flags import is_enabled

    _write_yaml(tmp_yaml, "MY_FLAG: true\n")
    monkeypatch.delenv("FEATURE_MY_FLAG", raising=False)

    assert is_enabled("MY_FLAG", default=False) is True


def test_is_enabled_falls_back_to_default(
    tmp_yaml: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When env unset and flag missing from yaml, default is returned."""
    from app.core.feature_flags import is_enabled

    _write_yaml(tmp_yaml, "OTHER_FLAG: true\n")
    monkeypatch.delenv("FEATURE_MISSING_FLAG", raising=False)

    assert is_enabled("MISSING_FLAG", default=False) is False
    assert is_enabled("MISSING_FLAG", default=True) is True


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("true", True), ("TRUE", True), ("True", True),
        ("1", True), ("yes", True), ("YES", True),
        ("false", False), ("FALSE", False),
        ("0", False), ("no", False), ("", False),
    ],
)
def test_env_var_parsing_truthy(
    tmp_yaml: Path, monkeypatch: pytest.MonkeyPatch,
    raw: str, expected: bool,
) -> None:
    """FEATURE_X env var parses common truthy/falsy string forms."""
    from app.core.feature_flags import is_enabled

    _write_yaml(tmp_yaml, "")  # ensure yaml has no opinion
    monkeypatch.setenv("FEATURE_X", raw)

    assert is_enabled("X") is expected


# -------------------- Rate limiter (pure unit) --------------------


def test_rate_limit_allows_under_threshold(tmp_yaml: Path) -> None:
    """Under 10 toggles per hour for the same actor: allowed."""
    from app.core.feature_flags import _check_rate_limit

    actor_hash = "hash-1"
    for _ in range(10):
        assert _check_rate_limit(actor_hash) is True


def test_rate_limit_blocks_over_threshold(tmp_yaml: Path) -> None:
    """11th toggle in one hour for the same actor is rejected."""
    from app.core.feature_flags import _check_rate_limit

    actor_hash = "hash-2"
    for _ in range(10):
        assert _check_rate_limit(actor_hash) is True
    assert _check_rate_limit(actor_hash) is False


def test_rate_limit_evicts_old_entries(tmp_yaml: Path) -> None:
    """Entries older than one hour do not count against the quota."""
    import app.core.feature_flags as ff

    actor_hash = "hash-3"
    old = datetime.now(timezone.utc) - timedelta(hours=2)
    ff._RATE_LIMITER[actor_hash] = [old] * 15

    assert ff._check_rate_limit(actor_hash) is True


# -------------------- Admin endpoint (integration) --------------------


@pytest_asyncio.fixture
async def admin_test_engine(tmp_path, monkeypatch):
    """Fresh SQLite engine with m001 + m002 applied so feature_flag_audit exists.

    Patches ``get_settings`` so both auth (admin_api_key) and
    :mod:`app.core.feature_flags` (database_url) see the test-scoped values.
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core import database as db_module
    from app.core.config import get_settings
    from app.core.migrations import m001_initial, m002_s12_worker_companion

    get_settings.cache_clear()

    db_path = tmp_path / "admin.db"
    sync_conn = sqlite3.connect(str(db_path))
    try:
        m001_initial.upgrade(sync_conn)
        m002_s12_worker_companion.upgrade(sync_conn)
        sync_conn.commit()
    finally:
        sync_conn.close()

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}", echo=False,
    )
    old_engine = db_module._engine
    old_factory = db_module._async_session_factory
    db_module._engine = engine
    db_module._async_session_factory = None

    settings_stub = MagicMock()
    settings_stub.admin_api_key = _ADMIN_KEY
    settings_stub.database_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setattr("app.core.auth.get_settings", lambda: settings_stub)
    monkeypatch.setattr(
        "app.core.feature_flags.get_settings", lambda: settings_stub, raising=False,
    )

    yield db_path

    await engine.dispose()
    db_module._engine = old_engine
    db_module._async_session_factory = old_factory


@pytest.fixture
def reset_flag_state(tmp_path, monkeypatch):
    """Reset in-memory feature-flag state between tests."""
    import app.core.feature_flags as ff

    yaml_path = tmp_path / "flags.yaml"
    yaml_path.write_text("ENABLE_AI_GENERATION: false\n")
    monkeypatch.setattr(ff, "_YAML_PATH", yaml_path)
    ff._reset_state_for_tests()
    yield
    ff._reset_state_for_tests()


@pytest.mark.asyncio
async def test_admin_endpoint_requires_admin_key(
    admin_test_engine, reset_flag_state,
):
    """No X-Admin-Key header → 422 (FastAPI missing-header default)."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/api/admin/flags/ENABLE_AI_GENERATION",
            json={"enabled": True, "reason": "test"},
        )
    assert resp.status_code in (401, 403, 422)


@pytest.mark.asyncio
async def test_admin_endpoint_wrong_key_403(
    admin_test_engine, reset_flag_state,
):
    """Wrong X-Admin-Key → 403."""
    from app.main import app

    with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/api/admin/flags/ENABLE_AI_GENERATION",
                headers={"X-Admin-Key": "wrong"},
                json={"enabled": True, "reason": "test"},
            )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_endpoint_writes_audit_row(
    admin_test_engine, reset_flag_state,
):
    """Successful toggle writes a full 7-field audit row with SHA256 hash."""
    from app.main import app

    with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/api/admin/flags/ENABLE_AI_GENERATION",
                headers={"X-Admin-Key": _ADMIN_KEY},
                json={"enabled": True, "reason": "unit-test toggle"},
            )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["flag_name"] == "ENABLE_AI_GENERATION"
    assert body["enabled"] is True
    assert "applied_at" in body

    conn = sqlite3.connect(str(admin_test_engine))
    try:
        row = conn.execute(
            "SELECT flag_name, old_value, new_value, reason, actor_token_hash, "
            "source_ip, timestamp FROM feature_flag_audit "
            "WHERE flag_name = ? ORDER BY id DESC LIMIT 1",
            ("ENABLE_AI_GENERATION",),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    flag_name, old_value, new_value, reason, actor_hash, source_ip, timestamp = row
    assert flag_name == "ENABLE_AI_GENERATION"
    assert old_value == "false"
    assert new_value == "true"
    assert reason == "unit-test toggle"
    assert actor_hash == hashlib.sha256(_ADMIN_KEY.encode()).hexdigest()
    assert source_ip  # non-empty
    assert timestamp  # non-empty ISO string


@pytest.mark.asyncio
async def test_actor_token_hash_is_sha256(
    admin_test_engine, reset_flag_state,
):
    """actor_token_hash is exactly hashlib.sha256(admin_key).hexdigest()."""
    from app.main import app

    with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            await c.post(
                "/api/admin/flags/FEATURE_NIGHTLY_ENABLED",
                headers={"X-Admin-Key": _ADMIN_KEY},
                json={"enabled": False, "reason": "maintenance"},
            )

    expected = hashlib.sha256(_ADMIN_KEY.encode()).hexdigest()
    conn = sqlite3.connect(str(admin_test_engine))
    try:
        row = conn.execute(
            "SELECT actor_token_hash FROM feature_flag_audit "
            "WHERE flag_name = ? ORDER BY id DESC LIMIT 1",
            ("FEATURE_NIGHTLY_ENABLED",),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    assert row[0] == expected
    # Sanity: actor_token_hash is never the plain admin key.
    assert row[0] != _ADMIN_KEY


@pytest.mark.asyncio
async def test_admin_endpoint_rate_limit_429(
    admin_test_engine, reset_flag_state,
):
    """11th rapid toggle with the same admin key returns 429."""
    from app.main import app

    with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            statuses = []
            for i in range(11):
                resp = await c.post(
                    "/api/admin/flags/FEATURE_EMAIL_SEND_ENABLED",
                    headers={"X-Admin-Key": _ADMIN_KEY},
                    json={"enabled": bool(i % 2), "reason": f"toggle-{i}"},
                )
                statuses.append(resp.status_code)

    assert statuses[:10] == [200] * 10
    assert statuses[10] == 429


@pytest.mark.asyncio
async def test_ai_generation_toggle_emits_warning(
    admin_test_engine, reset_flag_state, caplog: pytest.LogCaptureFixture,
):
    """Enabling ENABLE_AI_GENERATION logs a WARNING about PII / DPA."""
    from app.main import app

    caplog.set_level(logging.WARNING, logger="app.routes.admin_flags")

    with patch(_SETTINGS_PATCH, return_value=_mock_settings()):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/api/admin/flags/ENABLE_AI_GENERATION",
                headers={"X-Admin-Key": _ADMIN_KEY},
                json={"enabled": True, "reason": "pilot"},
            )

    assert resp.status_code == 200
    warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING
        and "AI generation enables LLM processing of worker PII" in r.getMessage()
    ]
    assert warnings, "Expected PII / DPA warning when enabling ENABLE_AI_GENERATION"
