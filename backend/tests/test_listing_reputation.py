"""Route tests for the reputation event recording API (T24.7).

Covers ``backend/app/routes/listing_reputation.py`` end-to-end with the
real DB layer. Calls the route handlers via their underlying coroutines
so the test stays on the same engine axes (sqlite + postgres) as the
rest of the verification suite.

Behaviours covered:

* Each value in ``EVENT_KINDS`` records a row.
* Role gating via ``any_of_roles("case_manager", "admin")``:
  case_manager OK, admin OK, sme_reviewer 403, anonymous 403.
* 404 when ``listing_id`` does not exist (route translates the
  ``ValueError`` raised by ``record_event``).
* Pydantic ``Literal`` rejects an unknown ``kind`` at the schema layer
  (caller-side test simulates the 422 by constructing the body model).
* ``session_id`` from an anonymous candidate is persisted on the event
  while ``recorded_by`` still comes from the gw_account cookie.
* Router is registered in :data:`app.routes.all_routers`.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_roles
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.auth_roles import any_of_roles
from app.core.listings_verification_schema import (
    EVENT_KINDS,
    apply_ddl as apply_verification_ddl,
)
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.routes import listing_reputation
from app.routes._auth_claim_helpers import build_account_cookie_value


# ---------------------------------------------------------------------------
# Engine + fixture stack (accounts + roles + verification DDL)
# ---------------------------------------------------------------------------


@pytest.fixture
async def reputation_engine(db_engine):
    """``db_engine`` plus accounts + roles + verification DDL."""
    async with db_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
        await conn.run_sync(apply_verification_ddl)
    return db_engine


@pytest.fixture
def session_factory(reputation_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        reputation_engine, class_=AsyncSession, expire_on_commit=False
    )


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


async def _make_account_with_roles(
    session: AsyncSession, email: str, roles: list[str]
) -> tuple[int, str]:
    """Create an account, grant *roles*, return (id, signed cookie)."""
    account_id = await queries_accounts.create_account(session, email=email)
    for r in roles:
        await queries_roles.grant_role(session, account_id, r)
    return account_id, build_account_cookie_value(account_id)


async def _make_listing(session: AsyncSession, *, title: str) -> int:
    """Insert one row into the legacy ``job_listings`` table."""
    result = await session.execute(
        text(
            "INSERT INTO job_listings (title, scraped_at) "
            "VALUES (:title, :scraped_at) RETURNING id"
        ),
        {"title": title, "scraped_at": "2026-05-08T00:00:00Z"},
    )
    new_id = int(result.scalar_one())
    await session.commit()
    return new_id


async def _resolve_account(session: AsyncSession, cookie: str) -> dict:
    """Resolve the gw_account cookie via the route's auth dep."""
    dep = any_of_roles("case_manager", "admin")
    return await dep(db=session, gw_account=cookie)


# ---------------------------------------------------------------------------
# Happy path — each event_kind recorded
# ---------------------------------------------------------------------------


@pytest.mark.anyio
@pytest.mark.parametrize("kind", list(EVENT_KINDS))
async def test_record_event_accepts_each_event_kind(session_factory, kind):
    """Each value in EVENT_KINDS produces a persisted row."""
    async with session_factory() as session:
        listing_id = await _make_listing(session, title=f"l-{kind}")
        _, cookie = await _make_account_with_roles(
            session, f"cm-{kind}@example.com", ["case_manager"]
        )
        account = await _resolve_account(session, cookie)
        body = listing_reputation.EventBody(kind=kind)
        result = await listing_reputation.record_event_endpoint(
            listing_id=listing_id, body=body,
            db=session, account=account,
        )
        row = await session.execute(
            text(
                "SELECT event_kind, recorded_by FROM listing_reputation_events "
                "WHERE id = :id"
            ),
            {"id": result["event_id"]},
        )
        mp = row.first()._mapping
    assert result["event_id"] > 0
    assert mp["event_kind"] == kind
    assert mp["recorded_by"] == account["id"]


@pytest.mark.anyio
async def test_record_event_persists_session_id_and_notes(session_factory):
    """Anonymous session_id from payload is stored on the event row."""
    async with session_factory() as session:
        listing_id = await _make_listing(session, title="ll-anon")
        _, cookie = await _make_account_with_roles(
            session, "cm-anon@example.com", ["case_manager"]
        )
        account = await _resolve_account(session, cookie)
        body = listing_reputation.EventBody(
            kind="placed",
            session_id="anon-sess-zzz",
            notes="walked into the office",
        )
        result = await listing_reputation.record_event_endpoint(
            listing_id=listing_id, body=body,
            db=session, account=account,
        )
        row = await session.execute(
            text(
                "SELECT session_id, notes, recorded_by "
                "FROM listing_reputation_events WHERE id = :id"
            ),
            {"id": result["event_id"]},
        )
        mp = row.first()._mapping
    assert mp["session_id"] == "anon-sess-zzz"
    assert mp["notes"] == "walked into the office"
    # recorded_by still comes from the cookie, NOT the payload.
    assert mp["recorded_by"] == account["id"]


# ---------------------------------------------------------------------------
# Role gating
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_record_event_admin_role_authorized(session_factory):
    """admin role is allowed by any_of_roles(case_manager, admin)."""
    async with session_factory() as session:
        listing_id = await _make_listing(session, title="ll-admin")
        _, cookie = await _make_account_with_roles(
            session, "admin@example.com", ["admin"]
        )
        account = await _resolve_account(session, cookie)
        body = listing_reputation.EventBody(kind="response_received")
        result = await listing_reputation.record_event_endpoint(
            listing_id=listing_id, body=body,
            db=session, account=account,
        )
    assert result["event_id"] > 0


@pytest.mark.anyio
async def test_record_event_anonymous_403(session_factory):
    """No gw_account cookie → 403 from any_of_roles."""
    async with session_factory() as session:
        dep = any_of_roles("case_manager", "admin")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=None)
    assert exc.value.status_code == 403
    assert "Authentication" in exc.value.detail


@pytest.mark.anyio
async def test_record_event_sme_reviewer_403(session_factory):
    """sme_reviewer role does NOT satisfy (case_manager, admin) gate."""
    async with session_factory() as session:
        _, cookie = await _make_account_with_roles(
            session, "sme@example.com", ["sme_reviewer"]
        )
        dep = any_of_roles("case_manager", "admin")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=cookie)
    assert exc.value.status_code == 403
    assert "Insufficient" in exc.value.detail


# ---------------------------------------------------------------------------
# Error translation
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_record_event_unknown_listing_returns_404(session_factory):
    """ValueError from record_event(unknown listing) → 404 HTTPException."""
    async with session_factory() as session:
        _, cookie = await _make_account_with_roles(
            session, "cm-404@example.com", ["case_manager"]
        )
        account = await _resolve_account(session, cookie)
        body = listing_reputation.EventBody(kind="ghosted")
        with pytest.raises(HTTPException) as exc:
            await listing_reputation.record_event_endpoint(
                listing_id=999_999, body=body,
                db=session, account=account,
            )
    assert exc.value.status_code == 404


def test_event_body_invalid_kind_rejected_by_pydantic():
    """Pydantic Literal rejects unknown kinds → auto-422 from FastAPI."""
    with pytest.raises(ValidationError):
        listing_reputation.EventBody(kind="not_a_real_event")


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------


def test_listing_reputation_router_registered():
    """listing_reputation_router is mounted in app.routes.all_routers."""
    from app.routes import all_routers
    from app.routes.listing_reputation import router as lr_router

    assert lr_router in all_routers
