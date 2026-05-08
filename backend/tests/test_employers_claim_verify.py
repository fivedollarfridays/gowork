"""Tests for the employer listing-claim verify endpoint (T24.4).

Covers ``GET /api/employers/claim/verify?token=…`` which:

* Validates a single-use claim token minted by T24.3's
  ``POST /api/employers/claim``.
* Returns 200 with ``{employer_account_id, listing_id,
  verification_tier, next_step}`` on success.
* Marks ``listing_claims.used_at`` and inserts a row into
  ``listing_verifications`` with the tier determined by the T24.3
  domain heuristic — ``employer_accounts.verification_status ==
  'admin_review'`` → ``admin_reviewed`` tier; otherwise
  ``claim_verified`` (and the employer is promoted to ``verified``).
* Sets the signed ``gw_employer_account`` cookie binding the browser
  to the employer identity. Parallel to S22's ``gw_account`` but
  scoped to the employer side; reuses ``audit_hash_salt``.
* Returns a uniform 401 (byte-identical body) for invalid / expired /
  already-used tokens — same anti-oracle posture as S22's auth claim.
* Returns 409 when ``listing_verifications`` already exists under a
  *different* employer.

Schema strategy mirrors :mod:`tests.test_employers_claim` — apply the
identity + verification DDL on top of the legacy m001..m010 schema.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_listings_verification
from app.core._listings_verification_internals import hash_claim_token
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.listings_verification_schema import (
    apply_ddl as apply_verification_ddl,
)


# -------------------- Fixtures --------------------


@pytest.fixture
async def employers_engine(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_verification_ddl)
    return test_engine


@pytest.fixture
def session_factory(employers_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        employers_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def verify_client(employers_engine, client):
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
    """Insert one employer_accounts row directly with an explicit status."""
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


async def _mint_token(
    session_factory, *, listing_id: int, email: str
) -> str:
    """Mint a claim token via the public helper, return the raw token."""
    async with session_factory() as session:
        raw_token, _claim_id = (
            await queries_listings_verification.mint_listing_claim_token(
                session,
                listing_id=listing_id,
                claimant_email=email,
                claimant_account_id=None,
            )
        )
    return raw_token


async def _force_expire_claim(session_factory, raw_token: str) -> None:
    token_hash = hash_claim_token(raw_token)
    past = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    ).isoformat()
    async with session_factory() as session:
        await session.execute(
            text(
                "UPDATE listing_claims SET expires_at = :exp "
                "WHERE claim_token_hash = :h"
            ),
            {"exp": past, "h": token_hash},
        )
        await session.commit()


async def _employer_status(session: AsyncSession, employer_id: int) -> str:
    result = await session.execute(
        text(
            "SELECT verification_status FROM employer_accounts WHERE id = :id"
        ),
        {"id": employer_id},
    )
    return str(result.scalar_one())


async def _verification_for_listing(
    session: AsyncSession, listing_id: int
) -> dict | None:
    return await queries_listings_verification.get_verification_for_listing(
        session, listing_id
    )


# -------------------- Cycle 1: success on domain match --------------------


@pytest.mark.anyio
async def test_verify_match_returns_claim_verified_tier(
    verify_client, session_factory
):
    """Domain matches company → tier=claim_verified + next_step=intake."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Forklift", company="ACME Hiring Inc"
        )
        employer_id = await _seed_employer(
            session, name="acmehiring.com", domain="acmehiring.com",
            status="pending",
        )

    raw_token = await _mint_token(
        session_factory, listing_id=listing_id, email="hr@acmehiring.com"
    )

    resp = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["employer_account_id"] == employer_id
    assert body["listing_id"] == listing_id
    assert body["verification_tier"] == "claim_verified"
    assert body["next_step"] == "intake"


@pytest.mark.anyio
async def test_verify_match_creates_verification_row_and_promotes_employer(
    verify_client, session_factory
):
    """Successful match writes listing_verifications + flips employer to verified."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Cook", company="Goodwill Industries"
        )
        employer_id = await _seed_employer(
            session, name="goodwill.org", domain="goodwill.org",
            status="pending",
        )

    raw_token = await _mint_token(
        session_factory, listing_id=listing_id, email="ops@goodwill.org"
    )

    resp = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert resp.status_code == 200

    async with session_factory() as session:
        verification = await _verification_for_listing(session, listing_id)
        assert verification is not None
        assert verification["verification_tier"] == "claim_verified"
        assert int(verification["employer_account_id"]) == employer_id
        # Employer was 'pending' → must now be 'verified'.
        assert await _employer_status(session, employer_id) == "verified"


@pytest.mark.anyio
async def test_verify_sets_signed_employer_cookie(
    verify_client, session_factory
):
    """Successful verify returns the gw_employer_account cookie."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Driver", company="ACME Hiring Inc"
        )
        await _seed_employer(
            session, name="acmehiring.com", domain="acmehiring.com",
            status="pending",
        )

    raw_token = await _mint_token(
        session_factory, listing_id=listing_id, email="hr@acmehiring.com"
    )

    resp = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert resp.status_code == 200
    set_cookie = resp.headers.get("set-cookie", "")
    assert "gw_employer_account=" in set_cookie
    # Required attributes mirror gw_account.
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()
    assert "samesite" in set_cookie.lower()


# -------------------- Cycle 2: domain mismatch → admin_reviewed --------------------


@pytest.mark.anyio
async def test_verify_mismatch_uses_admin_reviewed_tier(
    verify_client, session_factory
):
    """Domain mismatch (employer in admin_review) → tier=admin_reviewed."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Welder", company="ACME Hiring Inc"
        )
        employer_id = await _seed_employer(
            session, name="randomshell.io", domain="randomshell.io",
            status="admin_review",
        )

    raw_token = await _mint_token(
        session_factory,
        listing_id=listing_id,
        email="alice@randomshell.io",
    )

    resp = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verification_tier"] == "admin_reviewed"
    assert body["employer_account_id"] == employer_id

    async with session_factory() as session:
        verification = await _verification_for_listing(session, listing_id)
        assert verification is not None
        assert verification["verification_tier"] == "admin_reviewed"
        # admin_review status is NOT auto-promoted — admin must approve.
        assert (
            await _employer_status(session, employer_id) == "admin_review"
        )


# -------------------- Cycle 3: uniform 401 (no oracle) --------------------


@pytest.mark.anyio
async def test_verify_invalid_token_returns_401(verify_client):
    """An unknown token yields 401."""
    resp = await verify_client.get(
        "/api/employers/claim/verify?token=not-a-real-token"
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_verify_expired_token_returns_401(
    verify_client, session_factory
):
    """A token whose expires_at has passed yields 401."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="J", company="ACME"
        )
        await _seed_employer(
            session, name="acme.com", domain="acme.com", status="pending"
        )

    raw_token = await _mint_token(
        session_factory, listing_id=listing_id, email="hr@acme.com"
    )
    await _force_expire_claim(session_factory, raw_token)

    resp = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_verify_replayed_token_returns_401(
    verify_client, session_factory
):
    """A token already consumed yields 401 on replay."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="J", company="ACME"
        )
        await _seed_employer(
            session, name="acme.com", domain="acme.com", status="pending"
        )

    raw_token = await _mint_token(
        session_factory, listing_id=listing_id, email="hr@acme.com"
    )

    first = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert first.status_code == 200

    second = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert second.status_code == 401


@pytest.mark.anyio
async def test_verify_failure_modes_share_uniform_response(
    verify_client, session_factory
):
    """Invalid / expired / replayed all yield byte-identical bodies."""
    # Invalid (never existed)
    r_invalid = await verify_client.get(
        "/api/employers/claim/verify?token=neverwas"
    )

    # Expired
    async with session_factory() as session:
        l_exp = await _seed_listing(
            session, title="J", company="ACME"
        )
        await _seed_employer(
            session, name="acme.com", domain="acme.com", status="pending"
        )
    expired_token = await _mint_token(
        session_factory, listing_id=l_exp, email="hr@acme.com"
    )
    await _force_expire_claim(session_factory, expired_token)
    r_expired = await verify_client.get(
        f"/api/employers/claim/verify?token={expired_token}"
    )

    # Replayed
    async with session_factory() as session:
        l_rep = await _seed_listing(
            session, title="J2", company="ACME"
        )
    replay_token = await _mint_token(
        session_factory, listing_id=l_rep, email="hr@acme.com"
    )
    await verify_client.get(
        f"/api/employers/claim/verify?token={replay_token}"
    )
    r_replayed = await verify_client.get(
        f"/api/employers/claim/verify?token={replay_token}"
    )

    assert r_invalid.status_code == 401
    assert r_expired.status_code == 401
    assert r_replayed.status_code == 401
    # Byte-identical body across all three.
    assert r_invalid.content == r_expired.content == r_replayed.content


# -------------------- Cycle 4: cross-account 409 --------------------


@pytest.mark.anyio
async def test_verify_cross_employer_conflict_returns_409(
    verify_client, session_factory
):
    """Listing already verified by employer A → claim from employer B → 409."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="J", company="ACME Hiring Inc"
        )
        employer_a = await _seed_employer(
            session, name="acmehiring.com", domain="acmehiring.com",
            status="verified",
        )
        # Pre-create a verification owned by employer A.
        await queries_listings_verification.create_verification(
            session,
            listing_id=listing_id,
            employer_account_id=employer_a,
            tier="claim_verified",
            verified_by=0,
        )
        # Employer B exists and lays claim to the same listing.
        await _seed_employer(
            session, name="otherco.com", domain="otherco.com",
            status="pending",
        )

    raw_token = await _mint_token(
        session_factory, listing_id=listing_id, email="hr@otherco.com"
    )

    resp = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert resp.status_code == 409

    # Original ownership preserved.
    async with session_factory() as session:
        verification = await _verification_for_listing(session, listing_id)
        assert int(verification["employer_account_id"]) == employer_a


@pytest.mark.anyio
async def test_verify_token_consumed_even_on_409(
    verify_client, session_factory
):
    """Token is single-use across all outcomes — a 409 still burns it."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="J", company="ACME Hiring Inc"
        )
        employer_a = await _seed_employer(
            session, name="acmehiring.com", domain="acmehiring.com",
            status="verified",
        )
        await queries_listings_verification.create_verification(
            session,
            listing_id=listing_id,
            employer_account_id=employer_a,
            tier="claim_verified",
            verified_by=0,
        )
        await _seed_employer(
            session, name="otherco.com", domain="otherco.com",
            status="pending",
        )

    raw_token = await _mint_token(
        session_factory, listing_id=listing_id, email="hr@otherco.com"
    )

    first = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert first.status_code == 409

    second = await verify_client.get(
        f"/api/employers/claim/verify?token={raw_token}"
    )
    assert second.status_code == 401


# -------------------- Cycle 5: cookie helpers --------------------


def test_employer_cookie_round_trip():
    """build → verify yields the original employer_account_id."""
    from app.routes._employer_claim_helpers import (
        build_employer_cookie_value,
        verify_employer_cookie,
    )

    value = build_employer_cookie_value(42)
    assert verify_employer_cookie(value) == 42


def test_employer_cookie_rejects_account_cookie_format():
    """A gw_account-shaped value (no `emp:` prefix) MUST NOT validate."""
    from app.routes._auth_claim_helpers import build_account_cookie_value
    from app.routes._employer_claim_helpers import verify_employer_cookie

    account_cookie = build_account_cookie_value(42)
    # Different prefix → HMAC msg differs → must be rejected.
    assert verify_employer_cookie(account_cookie) is None


def test_employer_cookie_rejects_tampered_signature():
    """Changing the id half invalidates the HMAC."""
    from app.routes._employer_claim_helpers import (
        build_employer_cookie_value,
        verify_employer_cookie,
    )

    value = build_employer_cookie_value(42)
    # Swap id 42 → 43 keeps the format but breaks the HMAC.
    tampered = value.replace("emp:42:", "emp:43:")
    assert verify_employer_cookie(tampered) is None


def test_employer_cookie_rejects_missing_or_malformed():
    """None / empty / malformed values return None."""
    from app.routes._employer_claim_helpers import verify_employer_cookie

    assert verify_employer_cookie(None) is None
    assert verify_employer_cookie("") is None
    assert verify_employer_cookie("not-a-cookie") is None
    assert verify_employer_cookie("emp:abc:deadbeef") is None
    assert verify_employer_cookie("emp:-1:deadbeef") is None
