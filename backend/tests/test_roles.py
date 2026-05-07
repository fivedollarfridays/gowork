"""Tests for the role layer (T22.6).

Covers the ``account_roles`` table, the CRUD helpers in
:mod:`app.core.queries_roles`, and the ``require_role`` FastAPI
dependency in :mod:`app.core.auth_roles`.

Schema strategy mirrors :mod:`backend.tests.test_accounts` — apply
the identity DDL on top of the legacy ``db_engine`` schema, then
layer the roles DDL via :func:`app.core.roles_schema.apply_ddl`.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_roles
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.auth_roles import require_role
from app.core.roles_schema import apply_ddl as apply_roles_ddl


@pytest.fixture
async def roles_engine(db_engine):
    """``db_engine`` plus accounts + roles DDL applied on top."""
    async with db_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
    return db_engine


@pytest.fixture
def session_factory(roles_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        roles_engine, class_=AsyncSession, expire_on_commit=False
    )


# ---------------------------------------------------------------------------
# Schema + grant/has — happy path
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_account_roles_table_exists(session_factory):
    """Sanity: roles DDL created an account_roles table we can query."""
    async with session_factory() as session:
        # Empty SELECT is enough to prove the table exists on both engines.
        result = await session.execute(
            text("SELECT account_id, role_name, granted_at FROM account_roles")
        )
        assert result.first() is None


@pytest.mark.anyio
async def test_grant_role_persists_row(session_factory):
    """grant_role inserts an (account_id, role_name) row with granted_at."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="admin@example.com"
        )
        await queries_roles.grant_role(session, account_id, "admin")

        result = await session.execute(
            text(
                "SELECT role_name, granted_at FROM account_roles "
                "WHERE account_id = :aid"
            ),
            {"aid": account_id},
        )
        row = result.first()
        assert row is not None
        assert row._mapping["role_name"] == "admin"
        assert row._mapping["granted_at"] is not None


@pytest.mark.anyio
async def test_account_has_role_true_after_grant(session_factory):
    """account_has_role returns True after grant_role for the same role."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="admin2@example.com"
        )
        await queries_roles.grant_role(session, account_id, "admin")
        assert await queries_roles.account_has_role(
            session, account_id, "admin"
        ) is True


@pytest.mark.anyio
async def test_account_has_role_false_when_missing(session_factory):
    """account_has_role returns False for an unrelated role / unknown id."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="nobody@example.com"
        )
        # No roles granted at all
        assert await queries_roles.account_has_role(
            session, account_id, "admin"
        ) is False
        # Role granted, but a different one
        await queries_roles.grant_role(session, account_id, "case_manager")
        assert await queries_roles.account_has_role(
            session, account_id, "admin"
        ) is False
        # Unknown account id
        assert await queries_roles.account_has_role(
            session, 99999, "admin"
        ) is False


# ---------------------------------------------------------------------------
# list + revoke
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_roles_returns_all_granted(session_factory):
    """An account can hold multiple roles; list returns each one."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="multi@example.com"
        )
        for role in ("case_manager", "sme_reviewer", "admin"):
            await queries_roles.grant_role(session, account_id, role)

        roles = await queries_roles.list_roles_for_account(session, account_id)
        assert sorted(roles) == ["admin", "case_manager", "sme_reviewer"]


@pytest.mark.anyio
async def test_list_roles_empty_for_unknown_or_unrolled(session_factory):
    """An account with no grants — and an unknown id — return []."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="empty@example.com"
        )
        assert await queries_roles.list_roles_for_account(
            session, account_id
        ) == []
        assert await queries_roles.list_roles_for_account(
            session, 99999
        ) == []


@pytest.mark.anyio
async def test_revoke_role_removes_row(session_factory):
    """revoke_role drops the (account, role) pair; has_role flips False."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="revoke@example.com"
        )
        await queries_roles.grant_role(session, account_id, "admin")
        await queries_roles.grant_role(session, account_id, "case_manager")

        await queries_roles.revoke_role(session, account_id, "admin")

        assert await queries_roles.account_has_role(
            session, account_id, "admin"
        ) is False
        # Other role untouched
        assert await queries_roles.account_has_role(
            session, account_id, "case_manager"
        ) is True


@pytest.mark.anyio
async def test_revoke_role_idempotent_when_missing(session_factory):
    """Revoking a role that was never granted is a noop, not an error."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="noop@example.com"
        )
        # Should not raise even though no row exists
        await queries_roles.revoke_role(session, account_id, "admin")
        assert await queries_roles.list_roles_for_account(
            session, account_id
        ) == []


# ---------------------------------------------------------------------------
# Constraints — idempotency, enum, multi-role
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_grant_role_idempotent(session_factory):
    """Granting the same role twice is safe (no duplicate, no error)."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="idem@example.com"
        )
        await queries_roles.grant_role(session, account_id, "admin")
        await queries_roles.grant_role(session, account_id, "admin")

        roles = await queries_roles.list_roles_for_account(session, account_id)
        assert roles == ["admin"]


@pytest.mark.anyio
async def test_grant_role_rejects_invalid_enum(session_factory):
    """role_name CHECK constraint rejects values outside the enum."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="bad@example.com"
        )
        with pytest.raises(Exception):  # IntegrityError on either dialect
            await queries_roles.grant_role(session, account_id, "superuser")


@pytest.mark.anyio
async def test_one_account_can_hold_all_four_roles(session_factory):
    """Roles are not exclusive — one account can hold every role."""
    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="all@example.com"
        )
        all_roles = ["case_manager", "sme_reviewer", "dao_reviewer", "admin"]
        for role in all_roles:
            await queries_roles.grant_role(session, account_id, role)
        roles = await queries_roles.list_roles_for_account(session, account_id)
        assert sorted(roles) == sorted(all_roles)


# ---------------------------------------------------------------------------
# require_role FastAPI dependency
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_require_role_403_when_anonymous(session_factory):
    """Missing/None gw_account cookie -> 403 Authentication required."""
    async with session_factory() as session:
        dep = require_role("admin")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=None)
        assert exc.value.status_code == 403
        assert "Authentication" in exc.value.detail


@pytest.mark.anyio
async def test_require_role_403_when_missing_role(session_factory):
    """Valid signed cookie but account lacks the required role -> 403."""
    from app.routes._auth_claim_helpers import build_account_cookie_value

    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="caseworker@example.com"
        )
        await queries_roles.grant_role(session, account_id, "case_manager")
        cookie = build_account_cookie_value(account_id)

        dep = require_role("admin")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=cookie)
        assert exc.value.status_code == 403
        assert "Insufficient" in exc.value.detail


@pytest.mark.anyio
async def test_require_role_returns_account_when_authorized(session_factory):
    """Valid signed cookie + has role -> returns the account dict."""
    from app.routes._auth_claim_helpers import build_account_cookie_value

    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="boss@example.com"
        )
        await queries_roles.grant_role(session, account_id, "admin")
        cookie = build_account_cookie_value(account_id)

        dep = require_role("admin")
        result = await dep(db=session, gw_account=cookie)
        assert result is not None
        assert result["id"] == account_id
        assert result["email"] == "boss@example.com"


@pytest.mark.anyio
async def test_require_role_403_when_cookie_tampered(session_factory):
    """Tampered HMAC -> 403 Authentication required (oracle prevention)."""
    from app.routes._auth_claim_helpers import build_account_cookie_value

    async with session_factory() as session:
        account_id = await queries_accounts.create_account(
            session, email="admin@example.com"
        )
        await queries_roles.grant_role(session, account_id, "admin")
        # Truncate the HMAC half to invalidate the signature.
        good = build_account_cookie_value(account_id)
        bad = good[: good.rindex(".") + 5]

        dep = require_role("admin")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=bad)
        assert exc.value.status_code == 403
        assert "Authentication" in exc.value.detail
