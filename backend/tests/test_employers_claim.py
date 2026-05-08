"""Tests for the employer listing-claim initiation endpoint (T24.3).

Covers ``POST /api/employers/claim``:

* Always-202 contract (no enumeration on unknown listing, banned IP,
  rate-limited, etc.); empty body.
* ``listing_claims`` row minted with hashed token + 15-min expiry.
* ``employer_accounts`` row auto-created keyed by claimant-email domain
  if missing; case-insensitive domain lookup.
* Domain heuristic — ``job_listings.company`` fuzzy-matches the email
  domain → employer ``verification_status`` stays ``pending``;
  mismatch → flagged ``admin_review`` so T24.4/T24.5 verify can route
  the listing into the admin-review tier.
* SendGrid integration via the existing mock_provider — claim URL
  ``{FRONTEND_URL}/employers/claim?token={token}`` lands in payload.
* Tighter rate limits than candidate magic-link: 5/hour per IP,
  3/hour per email; over-limit calls still 202 but no email sent.
* Invalid email shape → 422 (the only non-202 success path; AC-mandated
  to reject before any DB lookup so the validator never touches state).

Schema strategy mirrors :mod:`tests.test_auth_magic_link` — apply the
identity-layer + verification DDL on top of the legacy m001..m010 schema
produced by ``init_db``. The route exercises the FastAPI app via the
shared ``client`` fixture and reaches the same DB through ``test_engine``.
"""

from __future__ import annotations

import re

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core._listings_verification_internals import hash_claim_token
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.listings_verification_schema import (
    apply_ddl as apply_verification_ddl,
)
from app.integrations.email import mock_provider, sendgrid_client


CLAIM_URL_RE = re.compile(
    r"https?://[^/]+/employers/claim\?token=([A-Za-z0-9_\-]{30,})"
)


# -------------------- Fixtures --------------------


@pytest.fixture
async def employers_engine(test_engine):
    """``test_engine`` plus accounts + listing-verification DDL."""
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
async def employers_client(employers_engine, client):
    """Async test client with verification + accounts DDL applied."""
    return client


@pytest.fixture
def mock_sendgrid(monkeypatch):
    fake = mock_provider.MockSendGridClient()
    monkeypatch.setattr(sendgrid_client, "_build_client", lambda: fake)
    monkeypatch.setenv("FEATURE_EMAIL_SEND_ENABLED", "true")
    return fake


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    from app.routes import employers as employers_module
    employers_module._email_limiter.clear()
    employers_module._ip_limiter.clear()
    yield
    employers_module._email_limiter.clear()
    employers_module._ip_limiter.clear()


# -------------------- Helpers --------------------


async def _seed_listing(
    session: AsyncSession, *, title: str, company: str | None
) -> int:
    """Insert one row into the legacy job_listings table, return id."""
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


async def _count_claims(session: AsyncSession, listing_id: int) -> int:
    result = await session.execute(
        text(
            "SELECT COUNT(*) FROM listing_claims WHERE listing_id = :lid"
        ),
        {"lid": listing_id},
    )
    return int(result.scalar() or 0)


async def _get_employer(session: AsyncSession, domain: str) -> dict | None:
    result = await session.execute(
        text("SELECT * FROM employer_accounts WHERE domain = :d"),
        {"d": domain},
    )
    row = result.first()
    return dict(row._mapping) if row else None


def _last_email_payload(fake: mock_provider.MockSendGridClient) -> dict:
    assert fake.calls, "expected SendGrid mock to receive a send"
    return fake.calls[-1]


def _extract_token_from_payload(payload: dict) -> str:
    body = payload.get("text", "") + " " + payload.get("html", "")
    match = CLAIM_URL_RE.search(body)
    assert match is not None, f"claim URL not found in payload: {payload!r}"
    return match.group(1)


# -------------------- Cycle 1: happy path 202 + claim row --------------------


@pytest.mark.anyio
async def test_claim_returns_202_and_mints_claim_row(
    employers_client, session_factory, mock_sendgrid
):
    """Happy path: known listing + matching domain → 202 + 1 claim row."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Forklift", company="ACME Hiring Inc"
        )

    resp = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": listing_id, "claimant_email": "hr@acmehiring.com"},
    )

    assert resp.status_code == 202
    assert resp.text == "" or resp.json() is None or resp.json() == {}

    async with session_factory() as session:
        assert await _count_claims(session, listing_id) == 1


@pytest.mark.anyio
async def test_claim_creates_employer_keyed_by_domain(
    employers_client, session_factory, mock_sendgrid
):
    """First claim from a domain auto-creates one employer_accounts row."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Janitor", company="Goodwill Industries"
        )

    resp = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": listing_id, "claimant_email": "team@goodwill.org"},
    )

    assert resp.status_code == 202
    async with session_factory() as session:
        employer = await _get_employer(session, "goodwill.org")
        assert employer is not None
        # domain heuristic: "Goodwill Industries" fuzzy-matches "goodwill.org"
        # → status remains 'pending' (will become 'verified' on T24.4 verify).
        assert employer["verification_status"] == "pending"


# -------------------- Cycle 2: invalid email --------------------


@pytest.mark.anyio
async def test_claim_invalid_email_returns_422(
    employers_client, session_factory, mock_sendgrid
):
    """Garbage email shape → 422 (validation runs before DB lookup)."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Driver", company="ACME"
        )

    resp = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": listing_id, "claimant_email": "not-an-email"},
    )

    assert resp.status_code == 422
    assert mock_sendgrid.calls == []


# -------------------- Cycle 3: SendGrid claim URL --------------------


@pytest.mark.anyio
async def test_claim_email_contains_claim_url_with_token(
    employers_client, session_factory, mock_sendgrid
):
    """SendGrid mock receives a payload containing the {FRONTEND_URL}/employers/claim URL."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Cook", company="ACME Kitchens"
        )

    resp = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": listing_id, "claimant_email": "boss@acme.co"},
    )
    assert resp.status_code == 202

    payload = _last_email_payload(mock_sendgrid)
    assert payload["to"] == "boss@acme.co"
    assert "listing_claim" in payload.get("categories", [])
    raw_token = _extract_token_from_payload(payload)

    expected_hash = hash_claim_token(raw_token)
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT 1 FROM listing_claims "
                "WHERE claim_token_hash = :h AND listing_id = :lid"
            ),
            {"h": expected_hash, "lid": listing_id},
        )
        assert result.first() is not None


# -------------------- Cycle 4: domain mismatch flags admin_review --------------------


@pytest.mark.anyio
async def test_claim_domain_mismatch_flags_admin_review(
    employers_client, session_factory, mock_sendgrid
):
    """Domain doesn't fuzzy-match company → employer flagged admin_review."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="Welder", company="ACME Hiring Inc"
        )

    resp = await employers_client.post(
        "/api/employers/claim",
        json={
            "listing_id": listing_id,
            "claimant_email": "alice@randomshell.io",
        },
    )

    assert resp.status_code == 202
    async with session_factory() as session:
        employer = await _get_employer(session, "randomshell.io")
        assert employer is not None
        assert employer["verification_status"] == "admin_review"


@pytest.mark.anyio
async def test_claim_reuses_existing_employer_by_domain(
    employers_client, session_factory, mock_sendgrid
):
    """Second claim from same domain reuses the existing employer row."""
    async with session_factory() as session:
        l1 = await _seed_listing(session, title="J1", company="ACME")
        l2 = await _seed_listing(session, title="J2", company="ACME")

    r1 = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": l1, "claimant_email": "a@acme.com"},
    )
    r2 = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": l2, "claimant_email": "b@acme.com"},
    )
    assert r1.status_code == 202
    assert r2.status_code == 202

    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT COUNT(*) FROM employer_accounts WHERE domain = :d"
            ),
            {"d": "acme.com"},
        )
        assert int(result.scalar() or 0) == 1


# -------------------- Cycle 5: rate limits --------------------


@pytest.mark.anyio
async def test_claim_per_email_rate_limit(
    employers_client, session_factory, mock_sendgrid
):
    """3/hour per-email: 4th request returns 202 but does NOT send."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="J", company="ACME"
        )

    email = "spammer@acme.com"
    for _ in range(3):
        resp = await employers_client.post(
            "/api/employers/claim",
            json={"listing_id": listing_id, "claimant_email": email},
        )
        assert resp.status_code == 202

    sends_before = len(mock_sendgrid.calls)
    resp = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": listing_id, "claimant_email": email},
    )
    assert resp.status_code == 202
    assert len(mock_sendgrid.calls) == sends_before


@pytest.mark.anyio
async def test_claim_per_ip_rate_limit(
    employers_client, session_factory, mock_sendgrid
):
    """5/hour per-IP: 6th request returns 202 but does NOT send."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="J", company="ACME"
        )

    # 5 distinct emails so per-email limiter never fires.
    for i in range(5):
        resp = await employers_client.post(
            "/api/employers/claim",
            json={
                "listing_id": listing_id,
                "claimant_email": f"ip{i}@distinct{i}.com",
            },
        )
        assert resp.status_code == 202

    sends_before = len(mock_sendgrid.calls)
    resp = await employers_client.post(
        "/api/employers/claim",
        json={
            "listing_id": listing_id,
            "claimant_email": "overflow@distinct.com",
        },
    )
    assert resp.status_code == 202
    assert len(mock_sendgrid.calls) == sends_before


# -------------------- Cycle 6: no-enumeration --------------------


@pytest.mark.anyio
async def test_claim_unknown_listing_id_returns_202(
    employers_client, mock_sendgrid
):
    """Unknown listing_id → still 202; no claim row, no SendGrid send."""
    resp = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": 999_999, "claimant_email": "x@example.com"},
    )
    assert resp.status_code == 202
    assert mock_sendgrid.calls == []


@pytest.mark.anyio
async def test_claim_unknown_and_known_listing_indistinguishable(
    employers_client, session_factory, mock_sendgrid
):
    """Known and unknown listing produce identical 202 response bodies."""
    async with session_factory() as session:
        listing_id = await _seed_listing(
            session, title="J", company="ACME"
        )

    r_known = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": listing_id, "claimant_email": "k@k.com"},
    )
    r_unknown = await employers_client.post(
        "/api/employers/claim",
        json={"listing_id": 9_999_999, "claimant_email": "u@u.com"},
    )
    assert r_known.status_code == 202
    assert r_unknown.status_code == 202
    assert r_known.text == r_unknown.text


# -------------------- Cycle 7: domain heuristic helper --------------------


def test_company_matches_domain_basic_prefix():
    """``ACME Hiring Inc`` ↔ ``acmehiring.com`` → match (prefix overlap)."""
    from app.routes.employers import _company_matches_domain
    assert _company_matches_domain("ACME Hiring Inc", "acmehiring.com") is True


def test_company_matches_domain_simple_company_subdomain():
    """``Goodwill Industries`` ↔ ``goodwill.org`` → match."""
    from app.routes.employers import _company_matches_domain
    assert _company_matches_domain("Goodwill Industries", "goodwill.org") is True


def test_company_matches_domain_unrelated_returns_false():
    """``ACME Hiring Inc`` ↔ ``randomshell.io`` → no match."""
    from app.routes.employers import _company_matches_domain
    assert _company_matches_domain("ACME Hiring Inc", "randomshell.io") is False


def test_company_matches_domain_handles_none_company():
    """Listing with NULL company is conservatively treated as no match."""
    from app.routes.employers import _company_matches_domain
    assert _company_matches_domain(None, "acme.com") is False
