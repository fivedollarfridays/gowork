"""Tests for the magic-link claim endpoint (T22.8).

Covers ``GET /api/auth/claim?token=…`` which:

* Validates a magic-link token from
  :func:`app.core.queries_accounts.mint_magic_link_credential` (T22.7).
* Returns a uniform 401 for invalid / expired / replayed tokens
  (no error oracle — same response body across all three failure
  modes so attackers cannot distinguish them).
* On success, marks ``account_credentials.used_at``, sets a session
  cookie binding the browser to the account, and (if the request
  carries an anonymous ``session_id``) calls ``claim_session()`` so
  the anonymous progress is durably linked to the account.
* If the ``session_id`` was already claimed by a *different* account,
  returns 409 Conflict (no silent overwrite).

Schema strategy mirrors :mod:`tests.test_auth_magic_link` — the
``accounts_engine`` fixture applies the identity-layer DDL on top of
the legacy m001..m010 schema produced by ``init_db`` so the magic-link
flow can write across both schemas in one transaction.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts
from app.core.accounts_schema import apply_ddl


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


# -------------------- Helpers --------------------


async def _mint_for_email(
    session_factory, email: str, *, ttl_minutes: int = 15
) -> tuple[int, str]:
    """Create an account and mint a magic-link token. Return (account_id, raw_token)."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(session, email=email)
        expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        raw_token, _credential_id = (
            await queries_accounts.mint_magic_link_credential(
                session, account_id=account_id, expires_at=expires
            )
        )
    return account_id, raw_token


async def _force_expire_credential(session_factory, raw_token: str) -> None:
    """Backdate the credential's ``expires_at`` so validation rejects it."""
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    past = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    ).isoformat()
    async with session_factory() as session:
        await session.execute(
            text(
                "UPDATE account_credentials SET expires_at = :exp "
                "WHERE credential_value_hash = :h"
            ),
            {"exp": past, "h": token_hash},
        )
        await session.commit()


async def _credential_used_at(
    session_factory, raw_token: str
) -> str | None:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT used_at FROM account_credentials "
                "WHERE credential_value_hash = :h"
            ),
            {"h": token_hash},
        )
        row = result.first()
        assert row is not None
        return row._mapping["used_at"]


# -------------------- Cycle 1: success --------------------


@pytest.mark.anyio
async def test_claim_valid_token_returns_account_id(
    auth_client, session_factory
):
    """A fresh, unexpired token yields a 200 with the account id."""
    account_id, raw_token = await _mint_for_email(
        session_factory, "alice@example.com"
    )

    resp = await auth_client.get(f"/api/auth/claim?token={raw_token}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["account_id"] == account_id
    assert body["claimed_session_ids"] == []


@pytest.mark.anyio
async def test_claim_valid_token_marks_used_at(
    auth_client, session_factory
):
    """Successful claim populates ``account_credentials.used_at``."""
    _, raw_token = await _mint_for_email(
        session_factory, "usedat@example.com"
    )
    assert await _credential_used_at(session_factory, raw_token) is None

    resp = await auth_client.get(f"/api/auth/claim?token={raw_token}")
    assert resp.status_code == 200

    used_at = await _credential_used_at(session_factory, raw_token)
    assert used_at is not None


@pytest.mark.anyio
async def test_claim_valid_token_sets_session_cookie(
    auth_client, session_factory
):
    """Successful claim returns a cookie binding the browser to the account."""
    _, raw_token = await _mint_for_email(
        session_factory, "cookie@example.com"
    )

    resp = await auth_client.get(f"/api/auth/claim?token={raw_token}")
    assert resp.status_code == 200
    # The cookie name MUST be present in the response Set-Cookie header.
    set_cookie = resp.headers.get("set-cookie", "")
    assert "gw_account=" in set_cookie
    # httpOnly + samesite are required attributes.
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()
    assert "samesite" in set_cookie.lower()


# -------------------- Cycle 2: uniform 401 (no oracle) --------------------


@pytest.mark.anyio
async def test_claim_invalid_token_returns_401(auth_client):
    """An unknown token yields 401 with a generic body."""
    resp = await auth_client.get("/api/auth/claim?token=not-a-real-token")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_claim_expired_token_returns_401(
    auth_client, session_factory
):
    """A token whose ``expires_at`` has passed yields 401."""
    _, raw_token = await _mint_for_email(
        session_factory, "expired@example.com"
    )
    await _force_expire_credential(session_factory, raw_token)

    resp = await auth_client.get(f"/api/auth/claim?token={raw_token}")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_claim_replayed_token_returns_401(
    auth_client, session_factory
):
    """A token already consumed (used_at set) yields 401 on replay."""
    _, raw_token = await _mint_for_email(
        session_factory, "replay@example.com"
    )

    first = await auth_client.get(f"/api/auth/claim?token={raw_token}")
    assert first.status_code == 200

    second = await auth_client.get(f"/api/auth/claim?token={raw_token}")
    assert second.status_code == 401


@pytest.mark.anyio
async def test_claim_failure_modes_share_uniform_response(
    auth_client, session_factory
):
    """Invalid / expired / replayed tokens all yield identical bodies.

    The response MUST NOT carry a distinguishing detail string —
    otherwise an attacker can probe whether a given token ever
    existed (oracle attack on token lifecycle).
    """
    # Invalid (never existed)
    r_invalid = await auth_client.get("/api/auth/claim?token=neverwas")

    # Expired
    _, expired_token = await _mint_for_email(
        session_factory, "uniform-expired@example.com"
    )
    await _force_expire_credential(session_factory, expired_token)
    r_expired = await auth_client.get(f"/api/auth/claim?token={expired_token}")

    # Replayed
    _, replay_token = await _mint_for_email(
        session_factory, "uniform-replay@example.com"
    )
    await auth_client.get(f"/api/auth/claim?token={replay_token}")
    r_replayed = await auth_client.get(
        f"/api/auth/claim?token={replay_token}"
    )

    assert r_invalid.status_code == 401
    assert r_expired.status_code == 401
    assert r_replayed.status_code == 401
    # Same body across all three failure modes.
    assert r_invalid.json() == r_expired.json() == r_replayed.json()


# -------------------- Cycle 3: session-claim --------------------


@pytest.mark.anyio
async def test_claim_with_session_id_claims_anonymous_session(
    auth_client, session_factory
):
    """A session_id on the request gets bound to the account on claim."""
    account_id, raw_token = await _mint_for_email(
        session_factory, "withsession@example.com"
    )
    session_id = "anon-sid-1"

    resp = await auth_client.get(
        f"/api/auth/claim?token={raw_token}&session_id={session_id}"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["account_id"] == account_id
    assert body["claimed_session_ids"] == [session_id]

    async with session_factory() as session:
        owner = await queries_accounts.get_account_for_session(
            session, session_id
        )
        assert owner is not None
        assert int(owner["id"]) == account_id


@pytest.mark.anyio
async def test_claim_pre_existing_anonymous_session_succeeds(
    auth_client, session_factory
):
    """An anon session_id that was never claimed before binds cleanly.

    This is the "save your progress" path — the user used the app
    anonymously, then later signs in via magic-link from the same
    browser. The session_id arrives on the claim request and we
    retroactively bind it.
    """
    account_id, raw_token = await _mint_for_email(
        session_factory, "save-progress@example.com"
    )
    session_id = "anon-pre-existing"

    # Sanity: the session is not yet claimed by anyone.
    async with session_factory() as session:
        assert (
            await queries_accounts.get_account_for_session(
                session, session_id
            )
            is None
        )

    resp = await auth_client.get(
        f"/api/auth/claim?token={raw_token}&session_id={session_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["account_id"] == account_id
    assert resp.json()["claimed_session_ids"] == [session_id]


@pytest.mark.anyio
async def test_claim_idempotent_when_session_already_owned_by_same_account(
    auth_client, session_factory
):
    """Re-claiming a session already owned by *this* account is a no-op."""
    account_id, raw_token = await _mint_for_email(
        session_factory, "idem@example.com"
    )
    session_id = "anon-idem"

    # Pre-bind the session to the same account directly.
    async with session_factory() as session:
        await queries_accounts.claim_session(session, account_id, session_id)

    resp = await auth_client.get(
        f"/api/auth/claim?token={raw_token}&session_id={session_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["claimed_session_ids"] == [session_id]


# -------------------- Cycle 4: cross-account 409 --------------------


@pytest.mark.anyio
async def test_claim_cross_account_conflict_returns_409(
    auth_client, session_factory
):
    """A session already owned by a different account yields 409."""
    # Account A owns the session first.
    other_account_id, _ = await _mint_for_email(
        session_factory, "owner@example.com"
    )
    session_id = "anon-conflict"
    async with session_factory() as session:
        await queries_accounts.claim_session(
            session, other_account_id, session_id
        )

    # Account B tries to claim the same session via its own magic-link.
    _new_account_id, raw_token = await _mint_for_email(
        session_factory, "stealer@example.com"
    )

    resp = await auth_client.get(
        f"/api/auth/claim?token={raw_token}&session_id={session_id}"
    )
    assert resp.status_code == 409
    # The original ownership is preserved.
    async with session_factory() as session:
        owner = await queries_accounts.get_account_for_session(
            session, session_id
        )
        assert owner is not None
        assert int(owner["id"]) == other_account_id

    # Single-use: the token is consumed even on 409, so account B cannot
    # re-POST and try a different session_id until expiry.
    second = await auth_client.get(
        f"/api/auth/claim?token={raw_token}&session_id=other-session"
    )
    assert second.status_code == 401, (
        "Token must be single-use across all outcomes — replay after 409 "
        "would let an attacker spam different session_ids until one is "
        "free, defeating the conflict guard."
    )
