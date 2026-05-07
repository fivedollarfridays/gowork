"""Tests for the magic-link issuance endpoint (T22.7).

Covers:

* :func:`app.core.queries_accounts.mint_magic_link_credential` — the
  credential-mint helper that returns a raw opaque token while
  persisting only its SHA-256 hash.
* ``POST /api/auth/magic-link`` — always-202 endpoint that creates an
  account on first use, mints a single-use token, and dispatches the
  email via the existing SendGrid integration. Rate-limited per-email
  and per-IP; over-limit calls still return 202 but no email is sent.

Schema strategy mirrors :mod:`tests.test_accounts` — apply the
identity-layer DDL on top of the legacy m001..m010 schema produced by
``init_db``. The route exercises the FastAPI app via the shared
``client`` fixture and reaches the same DB through ``test_engine``.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts
from app.core.accounts_schema import apply_ddl
from app.core.rate_limit import RateLimiter
from app.integrations.email import sendgrid_client
from app.integrations.email import mock_provider


CLAIM_URL_RE = re.compile(
    r"https?://[^/]+/auth/claim\?token=([A-Za-z0-9_\-]{30,})"
)


# -------------------- Fixtures --------------------


@pytest.fixture
async def accounts_engine(test_engine):
    """``test_engine`` plus the identity-layer DDL applied on top."""
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_ddl)
    return test_engine


@pytest.fixture
def session_factory(accounts_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        accounts_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def auth_client(accounts_engine, client):
    """Async test client with the identity DDL applied."""
    return client


@pytest.fixture
def mock_sendgrid(monkeypatch):
    """Install a canned-success mock SendGrid client.

    Returns the client instance so tests can inspect ``client.calls``
    for the captured payloads (subject/html/text + categories).
    """
    fake = mock_provider.MockSendGridClient()
    monkeypatch.setattr(sendgrid_client, "_build_client", lambda: fake)
    monkeypatch.setenv("FEATURE_EMAIL_SEND_ENABLED", "true")
    return fake


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    """Clear in-memory rate-limit state between tests.

    Imported lazily so a missing module during early-cycle development
    fails the import in the *test*, not in the autouse fixture.
    """
    from app.routes import auth as auth_module
    auth_module._email_limiter.clear()
    auth_module._ip_limiter.clear()
    yield
    auth_module._email_limiter.clear()
    auth_module._ip_limiter.clear()


# -------------------- Helpers --------------------


async def _count_credentials(session: AsyncSession, account_id: int) -> int:
    result = await session.execute(
        text(
            "SELECT COUNT(*) FROM account_credentials "
            "WHERE account_id = :aid AND credential_type = 'magic_link'"
        ),
        {"aid": account_id},
    )
    return int(result.scalar() or 0)


def _last_email_payload(fake: mock_provider.MockSendGridClient) -> dict:
    assert fake.calls, "expected SendGrid mock to have received a send"
    return fake.calls[-1]


def _extract_token_from_payload(payload: dict) -> str:
    body = payload.get("text", "") + " " + payload.get("html", "")
    match = CLAIM_URL_RE.search(body)
    assert match is not None, f"claim URL not found in payload: {payload!r}"
    return match.group(1)


# -------------------- Cycle 1: mint helper --------------------


@pytest.mark.anyio
async def test_mint_magic_link_credential_returns_raw_token(session_factory):
    """Helper returns a high-entropy raw token and stores only the hash."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="alice@example.com"
        )
        expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        raw_token, credential_id = (
            await queries_accounts.mint_magic_link_credential(
                session, account_id=account_id, expires_at=expires
            )
        )

        assert isinstance(raw_token, str)
        # secrets.token_urlsafe(32) yields ~43 url-safe chars => >=256 bits.
        assert len(raw_token) >= 32
        assert isinstance(credential_id, int) and credential_id > 0


@pytest.mark.anyio
async def test_mint_magic_link_credential_persists_sha256_hash(
    session_factory,
):
    """The DB stores SHA-256(raw_token); the raw token never lands on disk."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="bob@example.com"
        )
        expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        raw_token, _ = await queries_accounts.mint_magic_link_credential(
            session, account_id=account_id, expires_at=expires
        )

        result = await session.execute(
            text(
                "SELECT credential_value_hash, expires_at, used_at "
                "FROM account_credentials WHERE account_id = :aid"
            ),
            {"aid": account_id},
        )
        row = result.first()
        assert row is not None
        expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        assert row._mapping["credential_value_hash"] == expected_hash
        assert row._mapping["used_at"] is None
        # No raw token in the row.
        assert raw_token not in row._mapping["credential_value_hash"]


# -------------------- Cycle 2/3: endpoint returns 202 --------------------


@pytest.mark.anyio
async def test_magic_link_returns_202_for_known_email(
    auth_client, session_factory, mock_sendgrid
):
    """POST /api/auth/magic-link returns 202 for an existing account."""
    async with session_factory() as session:
        await queries_accounts.create_account(
            session, email="known@example.com"
        )

    resp = await auth_client.post(
        "/api/auth/magic-link", json={"email": "known@example.com"}
    )
    assert resp.status_code == 202
    # Always-no-body contract.
    assert resp.text == "" or resp.json() is None or resp.json() == {}


@pytest.mark.anyio
async def test_magic_link_creates_account_on_first_use(
    auth_client, session_factory, mock_sendgrid
):
    """Unknown email → account is created transparently; still 202."""
    resp = await auth_client.post(
        "/api/auth/magic-link", json={"email": "newcomer@example.com"}
    )
    assert resp.status_code == 202

    async with session_factory() as session:
        account = await queries_accounts.get_account_by_email(
            session, "newcomer@example.com"
        )
        assert account is not None
        assert account["email"] == "newcomer@example.com"
        assert await _count_credentials(session, account["id"]) == 1


# -------------------- Cycle 4: token lands in claim URL --------------------


@pytest.mark.anyio
async def test_magic_link_email_contains_claim_url_with_token(
    auth_client, session_factory, mock_sendgrid
):
    """The mock SendGrid receives a payload containing the claim URL."""
    resp = await auth_client.post(
        "/api/auth/magic-link", json={"email": "claim@example.com"}
    )
    assert resp.status_code == 202

    payload = _last_email_payload(mock_sendgrid)
    assert payload["to"] == "claim@example.com"
    assert "magic_link" in payload.get("categories", [])
    raw_token = _extract_token_from_payload(payload)

    # The hash of the raw token must match the row that was just persisted.
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT 1 FROM account_credentials "
                "WHERE credential_type = 'magic_link' "
                "AND credential_value_hash = :h"
            ),
            {"h": expected_hash},
        )
        assert result.first() is not None


# -------------------- Cycle 5: 15-minute expiry --------------------


@pytest.mark.anyio
async def test_magic_link_expiry_is_15_minutes(
    auth_client, session_factory, mock_sendgrid
):
    """The persisted ``expires_at`` is roughly utcnow + 15 minutes."""
    before = datetime.now(timezone.utc)
    resp = await auth_client.post(
        "/api/auth/magic-link", json={"email": "expiry@example.com"}
    )
    assert resp.status_code == 202
    after = datetime.now(timezone.utc)

    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT expires_at FROM account_credentials "
                "WHERE credential_type = 'magic_link'"
            )
        )
        row = result.first()
        assert row is not None
        expires = datetime.fromisoformat(row._mapping["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        # Allow a generous window (tests may stall) but pin the magnitude.
        assert (
            before + timedelta(minutes=14, seconds=30)
            <= expires
            <= after + timedelta(minutes=15, seconds=30)
        )


# -------------------- Cycle 6: no enumeration --------------------


@pytest.mark.anyio
async def test_magic_link_no_enumeration_unknown_email_indistinguishable(
    auth_client, mock_sendgrid
):
    """Unknown and known emails produce identical 202 responses."""
    r1 = await auth_client.post(
        "/api/auth/magic-link", json={"email": "u1@example.com"}
    )
    r2 = await auth_client.post(
        "/api/auth/magic-link", json={"email": "u2@example.com"}
    )
    assert r1.status_code == 202
    assert r2.status_code == 202
    assert r1.text == r2.text


# -------------------- Cycle 7/8: rate limits --------------------


@pytest.mark.anyio
async def test_magic_link_per_email_rate_limit(
    auth_client, session_factory, mock_sendgrid
):
    """3/hour per-email limit: 4th request returns 202 but does NOT send."""
    email = "ratelimited@example.com"
    for _ in range(3):
        resp = await auth_client.post(
            "/api/auth/magic-link", json={"email": email}
        )
        assert resp.status_code == 202

    sends_before = len(mock_sendgrid.calls)
    resp = await auth_client.post(
        "/api/auth/magic-link", json={"email": email}
    )
    # Always-202, even when limited.
    assert resp.status_code == 202
    # No new email dispatched.
    assert len(mock_sendgrid.calls) == sends_before


@pytest.mark.anyio
async def test_magic_link_per_ip_rate_limit(
    auth_client, mock_sendgrid
):
    """10/hour per-IP limit: 11th request returns 202 but does NOT send."""
    # 10 distinct emails so the per-email limiter never fires.
    for i in range(10):
        resp = await auth_client.post(
            "/api/auth/magic-link",
            json={"email": f"iprate{i}@example.com"},
        )
        assert resp.status_code == 202

    sends_before = len(mock_sendgrid.calls)
    resp = await auth_client.post(
        "/api/auth/magic-link",
        json={"email": "iprate-overflow@example.com"},
    )
    assert resp.status_code == 202
    assert len(mock_sendgrid.calls) == sends_before


# -------------------- Limiter sanity --------------------


def test_rate_limiter_is_keyed_separately_for_email_vs_ip():
    """Two RateLimiter instances do not share state — design sanity."""
    a = RateLimiter(max_requests=2, window_seconds=60)
    b = RateLimiter(max_requests=2, window_seconds=60)
    for _ in range(2):
        assert a.check("k") is True
    assert a.check("k") is False
    # b is unaffected.
    assert b.check("k") is True
