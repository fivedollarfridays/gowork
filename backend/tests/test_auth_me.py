"""Tests for ``GET /api/auth/me`` — read-side of the identity layer (T22.11).

The route reads the HMAC-signed ``gw_account`` cookie set by
``GET /api/auth/claim`` (T22.8) and returns the account binding so the
frontend can know whether the current browser is anonymous or claimed.

Contract:

* ``200`` with ``{"account_id": null, "email": null}`` when no cookie
  is present (anonymous-first invariant — never error on absence).
* ``200`` with ``{"account_id": int, "email": str}`` when the cookie
  is well-formed and the HMAC signature validates against the same
  ``audit_hash_salt`` used by ``set_account_cookie``.
* ``200`` with ``{"account_id": null, "email": null}`` when the cookie
  is malformed or the HMAC signature does NOT validate. We deliberately
  do NOT 401 on tampering because the legitimate "anonymous" answer is
  also 200-with-null — surfacing a 401 only for tampering would create
  a tampering oracle.

The route also requires a small read helper —
:func:`app.core.queries_accounts.get_account_by_id` — added alongside.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts
from app.core.accounts_schema import apply_ddl
from app.core.queries_roles import grant_role
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.routes._auth_claim_helpers import build_account_cookie_value


# -------------------- Fixtures --------------------


@pytest.fixture
async def accounts_engine(test_engine):
    """``test_engine`` plus the identity + roles DDL applied on top."""
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_ddl)
        await conn.run_sync(apply_roles_ddl)
    return test_engine


@pytest.fixture
def session_factory(accounts_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        accounts_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def auth_client(accounts_engine, client):
    return client


# -------------------- get_account_by_id helper --------------------


@pytest.mark.anyio
async def test_get_account_by_id_returns_row(session_factory):
    """Round-trip: create + lookup by id returns the expected email."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, "by-id@example.com",
        )
    async with session_factory() as session:
        row = await queries_accounts.get_account_by_id(session, account_id)
    assert row is not None
    assert row["email"] == "by-id@example.com"
    assert int(row["id"]) == account_id


@pytest.mark.anyio
async def test_get_account_by_id_missing_returns_none(session_factory):
    """Unknown ids return None — never raise."""
    async with session_factory() as session:
        row = await queries_accounts.get_account_by_id(session, 99999)
    assert row is None


# -------------------- /api/auth/me --------------------


@pytest.mark.anyio
async def test_me_anonymous_returns_null_account(auth_client):
    """No cookie -> 200 with null account/email and empty roles list."""
    resp = await auth_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json() == {"account_id": None, "email": None, "roles": []}


async def _get_with_cookie(client, value: str):
    """GET /api/auth/me with the gw_account cookie pre-set on the client.

    The httpx per-request ``cookies=`` kwarg is deprecated; setting it
    on the cookie jar mirrors the recommended pattern and avoids the
    DeprecationWarning during the test run.
    """
    client.cookies.set("gw_account", value)
    try:
        return await client.get("/api/auth/me")
    finally:
        client.cookies.delete("gw_account")


@pytest.mark.anyio
async def test_me_with_valid_cookie_returns_account(
    auth_client, session_factory
):
    """A correctly-signed cookie surfaces the bound account.

    Fresh accounts hold no roles, so ``roles`` is an empty list — never
    omitted (the frontend's ``AccountMe`` type relies on the field
    always being present so callers can branch without null-checks).
    """
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, "me@example.com"
        )
    cookie_value = build_account_cookie_value(account_id)

    resp = await _get_with_cookie(auth_client, cookie_value)
    assert resp.status_code == 200
    body = resp.json()
    assert body["account_id"] == account_id
    assert body["email"] == "me@example.com"
    assert body["roles"] == []


@pytest.mark.anyio
async def test_me_returns_granted_roles_for_authenticated_account(
    auth_client, session_factory
):
    """After ``grant_role`` the role appears in the ``/me`` response."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, "reviewer@example.com"
        )
        await grant_role(session, account_id, "sme_reviewer")
        await grant_role(session, account_id, "case_manager")
    cookie_value = build_account_cookie_value(account_id)

    resp = await _get_with_cookie(auth_client, cookie_value)
    assert resp.status_code == 200
    body = resp.json()
    assert body["account_id"] == account_id
    assert sorted(body["roles"]) == ["case_manager", "sme_reviewer"]


@pytest.mark.anyio
async def test_me_with_tampered_signature_returns_null(
    auth_client, session_factory
):
    """A cookie whose HMAC has been altered surfaces no account.

    Returning 200-with-null (rather than 401) preserves the anonymous-
    first invariant and avoids a tampering oracle.
    """
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, "tampered@example.com"
        )
    valid = build_account_cookie_value(account_id)
    # Replace the HMAC half with garbage, keep the id half.
    bad = f"{account_id}.deadbeef" + ("0" * 56)
    assert bad != valid  # sanity

    resp = await _get_with_cookie(auth_client, bad)
    assert resp.status_code == 200
    assert resp.json() == {"account_id": None, "email": None, "roles": []}


@pytest.mark.anyio
async def test_me_with_tampered_cookie_never_returns_roles(
    auth_client, session_factory
):
    """A tampered cookie MUST NOT leak the underlying account's roles.

    Even if an attacker correctly guesses an account id whose roles
    they want to probe, breaking the HMAC half drops them all the way
    back to anonymous — including ``roles: []`` — so the response
    shape gives no oracle on whether the underlying account has any
    privileges.
    """
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, "leaky@example.com"
        )
        await grant_role(session, account_id, "admin")
    bad = f"{account_id}.deadbeef" + ("0" * 56)

    resp = await _get_with_cookie(auth_client, bad)
    assert resp.status_code == 200
    assert resp.json() == {"account_id": None, "email": None, "roles": []}


@pytest.mark.anyio
async def test_me_with_malformed_cookie_returns_null(auth_client):
    """A cookie missing the ``id.hmac`` shape surfaces no account."""
    resp = await _get_with_cookie(auth_client, "not-a-valid-cookie-shape")
    assert resp.status_code == 200
    assert resp.json() == {"account_id": None, "email": None, "roles": []}


@pytest.mark.anyio
async def test_me_with_unknown_account_id_returns_null(auth_client):
    """A signed cookie pointing at a deleted/missing account -> null."""
    cookie_value = build_account_cookie_value(99_999)
    resp = await _get_with_cookie(auth_client, cookie_value)
    assert resp.status_code == 200
    assert resp.json() == {"account_id": None, "email": None, "roles": []}
