"""Tests for the employer listing-intake endpoint (T24.5).

Covers ``POST /api/employers/{employer_account_id}/listings/{listing_id}/intake``
which:

* Accepts the structured intake answers — must-haves, day-1 tasks,
  comp band, fair-chance willingness, additional notes — for a
  listing the caller has just verified ownership of.
* Pydantic-validates the body before any DB hit:
  ``must_haves`` and ``real_day1_tasks`` are non-empty lists of
  non-empty strings; ``comp_band_min`` and ``comp_band_max`` are
  positive ints with ``comp_band_min <= comp_band_max``.
* Gates on the signed ``gw_employer_account`` cookie matching the
  ``employer_account_id`` path param OR the caller holding the
  ``admin`` role via the ``gw_account`` cookie.
* Persists the JSON-encoded blob via
  :func:`queries_listings_verification.set_intake` and stamps
  ``intake_completed_at``.
* Returns the updated verification record (intake_json INCLUDED —
  caller is the verified employer who just submitted it; this is
  the read-after-write surface).

Schema strategy mirrors :mod:`tests.test_employers_claim_verify` —
apply the identity + verification DDL on top of the legacy m001..m010
schema. Adds the roles DDL so the admin-override path can be exercised.
"""

from __future__ import annotations

import json
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
from app.routes._employer_claim_helpers import (
    EMPLOYER_COOKIE_NAME,
    build_employer_cookie_value,
)


# -------------------- Fixtures --------------------


@pytest.fixture
async def intake_engine(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
        await conn.run_sync(apply_verification_ddl)
    return test_engine


@pytest.fixture
def session_factory(intake_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        intake_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def intake_client(intake_engine, client):
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
    session: AsyncSession, *, listing_id: int, employer_id: int
) -> None:
    await queries_listings_verification.create_verification(
        session,
        listing_id=listing_id,
        employer_account_id=employer_id,
        tier="claim_verified",
    )


async def _seed_admin_account(
    session: AsyncSession, email: str
) -> tuple[int, str]:
    """Create an account, grant admin, return (id, gw_account cookie)."""
    account_id = await queries_accounts.create_account(session, email=email)
    await queries_roles.grant_role(session, account_id, "admin")
    return account_id, build_account_cookie_value(account_id)


def _valid_body() -> dict:
    """Reusable valid payload for the happy paths."""
    return {
        "must_haves": ["valid driver's license", "ability to lift 50 lbs"],
        "nice_to_haves": ["forklift certification"],
        "real_day1_tasks": [
            "complete site safety walkthrough",
            "shadow a senior tech",
        ],
        "comp_band_min": 18,
        "comp_band_max": 24,
        "fair_chance_willingness": True,
        "additional_notes": "Background check is post-conditional offer.",
    }


# -------------------- Cycle 1: Pydantic validation --------------------


@pytest.mark.anyio
async def test_intake_rejects_empty_must_haves(intake_client, session_factory):
    """must_haves=[] → 422 from Pydantic before any DB hit."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Forklift", company="ACME Hiring Inc"
        )
        employer_id = await _seed_employer(
            session, name="acmehiring.com", domain="acmehiring.com",
            status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_id
        )

    body = _valid_body()
    body["must_haves"] = []
    resp = await intake_client.post(
        f"/api/employers/{employer_id}/listings/{listing_id}/intake",
        json=body,
        cookies={EMPLOYER_COOKIE_NAME: build_employer_cookie_value(employer_id)},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_intake_rejects_empty_real_day1_tasks(
    intake_client, session_factory
):
    """real_day1_tasks=[] → 422 from Pydantic."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Cook", company="Goodwill"
        )
        employer_id = await _seed_employer(
            session, name="goodwill.org", domain="goodwill.org",
            status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_id
        )

    body = _valid_body()
    body["real_day1_tasks"] = []
    resp = await intake_client.post(
        f"/api/employers/{employer_id}/listings/{listing_id}/intake",
        json=body,
        cookies={EMPLOYER_COOKIE_NAME: build_employer_cookie_value(employer_id)},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_intake_rejects_comp_band_min_greater_than_max(
    intake_client, session_factory
):
    """comp_band_min > comp_band_max → 422 (Pydantic field_validator)."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Driver", company="ACME"
        )
        employer_id = await _seed_employer(
            session, name="acme.com", domain="acme.com", status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_id
        )

    body = _valid_body()
    body["comp_band_min"] = 30
    body["comp_band_max"] = 20
    resp = await intake_client.post(
        f"/api/employers/{employer_id}/listings/{listing_id}/intake",
        json=body,
        cookies={EMPLOYER_COOKIE_NAME: build_employer_cookie_value(employer_id)},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_intake_rejects_negative_comp_band(intake_client, session_factory):
    """comp_band_min <= 0 → 422 (positive constraint)."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Driver", company="ACME"
        )
        employer_id = await _seed_employer(
            session, name="acme.com", domain="acme.com", status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_id
        )

    body = _valid_body()
    body["comp_band_min"] = -1
    resp = await intake_client.post(
        f"/api/employers/{employer_id}/listings/{listing_id}/intake",
        json=body,
        cookies={EMPLOYER_COOKIE_NAME: build_employer_cookie_value(employer_id)},
    )
    assert resp.status_code == 422


# -------------------- Cycle 2: Happy paths --------------------


@pytest.mark.anyio
async def test_intake_employer_cookie_persists_intake_and_returns_record(
    intake_client, session_factory
):
    """Verified employer with cookie → 200, intake persisted, full record returned."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Forklift", company="ACME Hiring Inc"
        )
        employer_id = await _seed_employer(
            session, name="acmehiring.com", domain="acmehiring.com",
            status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_id
        )

    body = _valid_body()
    resp = await intake_client.post(
        f"/api/employers/{employer_id}/listings/{listing_id}/intake",
        json=body,
        cookies={EMPLOYER_COOKIE_NAME: build_employer_cookie_value(employer_id)},
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    # intake_json INCLUDED in employer-private response.
    assert payload["listing_id"] == listing_id
    assert int(payload["employer_account_id"]) == employer_id
    assert payload["intake_completed_at"] is not None
    intake = json.loads(payload["intake_json"])
    assert intake["must_haves"] == body["must_haves"]
    assert intake["comp_band_min"] == 18
    assert intake["comp_band_max"] == 24
    assert intake["fair_chance_willingness"] is True

    # DB row reflects the persisted intake.
    async with session_factory() as session:
        row = (
            await queries_listings_verification.get_verification_for_listing(
                session, listing_id
            )
        )
        assert row is not None
        assert row["intake_completed_at"] is not None
        stored = json.loads(row["intake_json"])
        assert stored["real_day1_tasks"] == body["real_day1_tasks"]


@pytest.mark.anyio
async def test_intake_admin_override_via_gw_account_cookie(
    intake_client, session_factory
):
    """Caller with admin role (no employer cookie) → 200."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Welder", company="ACME"
        )
        employer_id = await _seed_employer(
            session, name="acme.com", domain="acme.com", status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_id
        )
        _, admin_cookie = await _seed_admin_account(
            session, "intake-admin@example.com"
        )

    resp = await intake_client.post(
        f"/api/employers/{employer_id}/listings/{listing_id}/intake",
        json=_valid_body(),
        cookies={SESSION_COOKIE_NAME: admin_cookie},
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert int(payload["employer_account_id"]) == employer_id


# -------------------- Cycle 3: Gating failures --------------------


@pytest.mark.anyio
async def test_intake_anonymous_returns_403(intake_client, session_factory):
    """No cookies at all → 403."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Driver", company="ACME"
        )
        employer_id = await _seed_employer(
            session, name="acme.com", domain="acme.com", status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_id
        )

    resp = await intake_client.post(
        f"/api/employers/{employer_id}/listings/{listing_id}/intake",
        json=_valid_body(),
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_intake_wrong_employer_cookie_returns_403(
    intake_client, session_factory
):
    """Cookie's employer id != path employer id → 403."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Driver", company="ACME"
        )
        employer_a = await _seed_employer(
            session, name="acme.com", domain="acme.com", status="verified",
        )
        employer_b = await _seed_employer(
            session, name="other.com", domain="other.com", status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_a
        )

    # Cookie binds employer B but the path targets employer A's listing.
    resp = await intake_client.post(
        f"/api/employers/{employer_a}/listings/{listing_id}/intake",
        json=_valid_body(),
        cookies={EMPLOYER_COOKIE_NAME: build_employer_cookie_value(employer_b)},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_intake_listing_owned_by_different_employer_returns_404(
    intake_client, session_factory
):
    """Cookie matches employer_account_id but the listing belongs to a different employer → 404."""
    async with session_factory() as session:
        # Listing verified by employer A.
        listing_id = await _seed_listing(
            session, title="Driver", company="ACME"
        )
        employer_a = await _seed_employer(
            session, name="acme.com", domain="acme.com", status="verified",
        )
        await _seed_verification(
            session, listing_id=listing_id, employer_id=employer_a
        )
        # Employer B exists but does NOT own this listing.
        employer_b = await _seed_employer(
            session, name="other.com", domain="other.com", status="verified",
        )

    # Cookie matches employer B and path uses employer B — but the listing
    # under that path is owned by employer A. Must 404 (not 403): the
    # caller is correctly authenticated as employer B, just targeting a
    # listing that doesn't belong to them.
    resp = await intake_client.post(
        f"/api/employers/{employer_b}/listings/{listing_id}/intake",
        json=_valid_body(),
        cookies={EMPLOYER_COOKIE_NAME: build_employer_cookie_value(employer_b)},
    )
    assert resp.status_code == 404
