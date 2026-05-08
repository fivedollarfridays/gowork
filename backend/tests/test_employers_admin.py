"""Tests for the admin claim-review dashboard endpoints (T24.9).

Covers the four routes mounted under
``/api/employers/admin/claims/...`` — all gated by
``require_role("admin")``:

* ``GET /api/employers/admin/claims/pending`` — admin queue read.
* ``GET /api/employers/admin/claims/{claim_id}`` — claim+listing+
  employer+verification detail.
* ``POST /api/employers/admin/claims/{claim_id}/approve`` — bumps the
  employer's ``verification_status`` to ``verified`` and refreshes the
  listing_verifications ``verified_at`` stamp; the verification tier
  stays at ``admin_reviewed``.
* ``DELETE /api/employers/admin/claims/{claim_id}`` — rejection;
  removes the claim + verification rows and sets the employer's
  ``verification_status`` to ``retired``.

Schema strategy mirrors :mod:`tests.test_employers_intake` — apply
identity + roles + verification DDL on top of the legacy m001..m010
schema. Admin role is granted via :mod:`queries_roles` and the
``gw_account`` cookie is signed via the S22 helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import (
    queries_accounts,
    queries_listings_verification,
    queries_roles,
)
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.listings_verification_schema import (
    apply_ddl as apply_verification_ddl,
)
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.routes._auth_claim_helpers import (
    SESSION_COOKIE_NAME,
    build_account_cookie_value,
)


# -------------------- Fixtures --------------------


@pytest.fixture
async def admin_engine(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
        await conn.run_sync(apply_verification_ddl)
    return test_engine


@pytest.fixture
def session_factory(admin_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        admin_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def admin_client(admin_engine, client):
    return client


# -------------------- Helpers --------------------


async def _seed_listing(
    session: AsyncSession, *, title: str, company: str | None
) -> int:
    result = await session.execute(
        text(
            "INSERT INTO job_listings (title, company, scraped_at) "
            "VALUES (:t, :c, :s) RETURNING id"
        ),
        {"t": title, "c": company, "s": "2026-05-08T00:00:00Z"},
    )
    new_id = int(result.scalar_one())
    await session.commit()
    return new_id


async def _seed_employer(
    session: AsyncSession, *, name: str, domain: str, status: str
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    result = await session.execute(
        text(
            "INSERT INTO employer_accounts "
            "(name, domain, verification_status, created_at) "
            "VALUES (:n, :d, :s, :ts) RETURNING id"
        ),
        {"n": name, "d": domain, "s": status, "ts": now},
    )
    new_id = int(result.scalar_one())
    await session.commit()
    return new_id


async def _seed_verification(
    session: AsyncSession, *, listing_id: int, employer_id: int,
    tier: str = "admin_reviewed",
) -> None:
    await queries_listings_verification.create_verification(
        session,
        listing_id=listing_id,
        employer_account_id=employer_id,
        tier=tier,
    )


async def _seed_claim(
    session: AsyncSession, *, listing_id: int, email: str
) -> int:
    """Mint a claim row, return its primary key (token discarded)."""
    _raw, claim_id = await (
        queries_listings_verification.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email=email,
            claimant_account_id=None,
        )
    )
    return claim_id


async def _seed_admin_account(
    session: AsyncSession, email: str
) -> tuple[int, str]:
    """Create an account, grant admin, return (id, gw_account cookie)."""
    account_id = await queries_accounts.create_account(session, email=email)
    await queries_roles.grant_role(session, account_id, "admin")
    return account_id, build_account_cookie_value(account_id)


async def _seed_non_admin_account(
    session: AsyncSession, email: str
) -> tuple[int, str]:
    """Create a regular account (no roles), return (id, gw_account cookie)."""
    account_id = await queries_accounts.create_account(session, email=email)
    return account_id, build_account_cookie_value(account_id)


async def _scenario_with_claim(
    session: AsyncSession, *, employer_status: str = "admin_review"
) -> tuple[int, int, int]:
    """Seed a complete admin-review scenario.

    Returns ``(claim_id, listing_id, employer_id)``. The verification
    row is at the ``admin_reviewed`` tier — the queue read should
    surface it.
    """
    listing_id = await _seed_listing(
        session, title="Forklift", company="ACME Hiring Inc"
    )
    employer_id = await _seed_employer(
        session, name="acmehiring.com", domain="acmehiring.com",
        status=employer_status,
    )
    await _seed_verification(
        session, listing_id=listing_id, employer_id=employer_id
    )
    claim_id = await _seed_claim(
        session, listing_id=listing_id,
        email="claimant@acmehiring.com",
    )
    return claim_id, listing_id, employer_id


# -------------------- Cycle 1: Anonymous + non-admin gating --------------------


@pytest.mark.anyio
async def test_pending_anonymous_returns_403(admin_client, session_factory):
    """No cookie → 403 from require_role('admin')."""
    resp = await admin_client.get("/api/employers/admin/claims/pending")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_pending_non_admin_returns_403(admin_client, session_factory):
    """Authenticated non-admin → 403 (insufficient permissions)."""
    async with session_factory() as session:
        _id, cookie = await _seed_non_admin_account(
            session, "user@example.com"
        )
    resp = await admin_client.get(
        "/api/employers/admin/claims/pending",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_detail_anonymous_returns_403(admin_client, session_factory):
    resp = await admin_client.get("/api/employers/admin/claims/1")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_approve_anonymous_returns_403(admin_client, session_factory):
    resp = await admin_client.post("/api/employers/admin/claims/1/approve")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_reject_anonymous_returns_403(admin_client, session_factory):
    resp = await admin_client.delete("/api/employers/admin/claims/1")
    assert resp.status_code == 403


# -------------------- Cycle 2: Pending queue (admin) --------------------


@pytest.mark.anyio
async def test_pending_admin_returns_queue(admin_client, session_factory):
    """Admin sees rows for verifications at the admin_reviewed tier."""
    async with session_factory() as session:
        claim_id, listing_id, employer_id = await _scenario_with_claim(
            session
        )
        _aid, cookie = await _seed_admin_account(
            session, "admin1@example.com"
        )

    resp = await admin_client.get(
        "/api/employers/admin/claims/pending",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert isinstance(rows, list)
    assert len(rows) == 1
    row = rows[0]
    assert row["listing_id"] == listing_id
    assert row["employer_account_id"] == employer_id
    assert row["verification_tier"] == "admin_reviewed"
    assert row["listing_title"] == "Forklift"
    assert row["employer_domain"] == "acmehiring.com"


@pytest.mark.anyio
async def test_pending_admin_empty_when_no_admin_review(
    admin_client, session_factory
):
    """Empty queue → 200 [].

    Verifications at non-admin_reviewed tiers must NOT appear.
    """
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Driver", company="ACME"
        )
        employer_id = await _seed_employer(
            session, name="acme.com", domain="acme.com", status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_id,
            tier="claim_verified",
        )
        _aid, cookie = await _seed_admin_account(
            session, "admin2@example.com"
        )

    resp = await admin_client.get(
        "/api/employers/admin/claims/pending",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200
    assert resp.json() == []


# -------------------- Cycle 3: Detail (admin) --------------------


@pytest.mark.anyio
async def test_detail_admin_returns_claim_and_listing(
    admin_client, session_factory
):
    """Admin sees claim + listing + employer + verification."""
    async with session_factory() as session:
        claim_id, listing_id, employer_id = await _scenario_with_claim(
            session
        )
        _aid, cookie = await _seed_admin_account(
            session, "admin3@example.com"
        )

    resp = await admin_client.get(
        f"/api/employers/admin/claims/{claim_id}",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["claim_id"] == claim_id
    assert body["claimant_email"] == "claimant@acmehiring.com"
    assert body["listing_id"] == listing_id
    assert body["listing_title"] == "Forklift"
    assert body["listing_company"] == "ACME Hiring Inc"
    assert body["employer_account_id"] == employer_id
    assert body["employer_domain"] == "acmehiring.com"
    assert body["verification_tier"] == "admin_reviewed"
    # No intake yet → null/None.
    assert body["intake_json"] is None


@pytest.mark.anyio
async def test_detail_unknown_claim_returns_404(
    admin_client, session_factory
):
    """Unknown claim_id → 404."""
    async with session_factory() as session:
        _aid, cookie = await _seed_admin_account(
            session, "admin4@example.com"
        )
    resp = await admin_client.get(
        "/api/employers/admin/claims/99999",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404


# -------------------- Cycle 4: Approve --------------------


@pytest.mark.anyio
async def test_approve_admin_promotes_employer_to_verified(
    admin_client, session_factory
):
    """Approve: employer.verification_status → verified; verification stays."""
    async with session_factory() as session:
        claim_id, listing_id, employer_id = await _scenario_with_claim(
            session
        )
        _aid, cookie = await _seed_admin_account(
            session, "admin5@example.com"
        )

    resp = await admin_client.post(
        f"/api/employers/admin/claims/{claim_id}/approve",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["claim_id"] == claim_id
    assert body["employer_account_id"] == employer_id
    assert body["verification_status"] == "verified"

    # DB reflects the promotion.
    async with session_factory() as session:
        row = await session.execute(
            text(
                "SELECT verification_status, verified_at FROM "
                "employer_accounts WHERE id = :id"
            ),
            {"id": employer_id},
        )
        emp = row.first()
        assert emp is not None
        assert emp._mapping["verification_status"] == "verified"
        assert emp._mapping["verified_at"] is not None
        # Verification row still exists at admin_reviewed tier.
        v_row = await session.execute(
            text(
                "SELECT verification_tier FROM listing_verifications "
                "WHERE listing_id = :lid"
            ),
            {"lid": listing_id},
        )
        v = v_row.first()
        assert v is not None
        assert v._mapping["verification_tier"] == "admin_reviewed"


@pytest.mark.anyio
async def test_approve_unknown_claim_returns_404(
    admin_client, session_factory
):
    """Approve on unknown claim → 404."""
    async with session_factory() as session:
        _aid, cookie = await _seed_admin_account(
            session, "admin6@example.com"
        )
    resp = await admin_client.post(
        "/api/employers/admin/claims/99999/approve",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404


# -------------------- Cycle 5: Reject --------------------


@pytest.mark.anyio
async def test_reject_admin_deletes_claim_and_verification(
    admin_client, session_factory
):
    """Reject: claim row + verification row deleted; employer retired."""
    async with session_factory() as session:
        claim_id, listing_id, employer_id = await _scenario_with_claim(
            session
        )
        _aid, cookie = await _seed_admin_account(
            session, "admin7@example.com"
        )

    resp = await admin_client.delete(
        f"/api/employers/admin/claims/{claim_id}",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 204

    async with session_factory() as session:
        c = await session.execute(
            text("SELECT id FROM listing_claims WHERE id = :id"),
            {"id": claim_id},
        )
        assert c.first() is None
        v = await session.execute(
            text(
                "SELECT id FROM listing_verifications "
                "WHERE listing_id = :lid"
            ),
            {"lid": listing_id},
        )
        assert v.first() is None
        emp = await session.execute(
            text(
                "SELECT verification_status FROM employer_accounts "
                "WHERE id = :id"
            ),
            {"id": employer_id},
        )
        emp_row = emp.first()
        assert emp_row is not None
        assert emp_row._mapping["verification_status"] == "retired"


@pytest.mark.anyio
async def test_reject_unknown_claim_returns_404(
    admin_client, session_factory
):
    """Reject on unknown claim → 404."""
    async with session_factory() as session:
        _aid, cookie = await _seed_admin_account(
            session, "admin8@example.com"
        )
    resp = await admin_client.delete(
        "/api/employers/admin/claims/99999",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404


# -------------------- Cycle 6: Non-admin write attempts --------------------


@pytest.mark.anyio
async def test_approve_non_admin_returns_403(admin_client, session_factory):
    async with session_factory() as session:
        claim_id, _lid, _eid = await _scenario_with_claim(session)
        _aid, cookie = await _seed_non_admin_account(
            session, "nope@example.com"
        )
    resp = await admin_client.post(
        f"/api/employers/admin/claims/{claim_id}/approve",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_reject_non_admin_returns_403(admin_client, session_factory):
    async with session_factory() as session:
        claim_id, _lid, _eid = await _scenario_with_claim(session)
        _aid, cookie = await _seed_non_admin_account(
            session, "nope2@example.com"
        )
    resp = await admin_client.delete(
        f"/api/employers/admin/claims/{claim_id}",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 403
