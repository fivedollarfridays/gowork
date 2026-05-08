"""Schema-sanity tests for the verification substrate (T24.1).

Exercises the four tables introduced by alembic revision 0014.
Layers the accounts + verification DDL on top of the legacy
``db_engine`` schema (which already contains ``job_listings`` from
m001). Covers table presence, ENUM CHECK enforcement, the
UNIQUE(listing_id) invariant on listing_verifications, the
reputation-event index, and the ENUM-tuple constants.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.listings_verification_schema import (
    EVENT_KINDS,
    SOURCE_TRUST_TIERS,
    VERIFICATION_STATUSES,
    VERIFICATION_TIERS,
    apply_ddl as apply_verification_ddl,
)


@pytest.fixture
async def verification_engine(db_engine):
    """``db_engine`` plus accounts + verification DDL applied on top."""
    async with db_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_verification_ddl)
    return db_engine


@pytest.fixture
def session_factory(verification_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        verification_engine, class_=AsyncSession, expire_on_commit=False
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_account(session: AsyncSession, email: str) -> int:
    """Create an account row and return its id."""
    return await queries_accounts.create_account(session, email=email)


async def _make_listing(session: AsyncSession, *, title: str) -> int:
    """Insert a job_listings row and return its id (RETURNING-based)."""
    result = await session.execute(
        text(
            "INSERT INTO job_listings (title, scraped_at) "
            "VALUES (:title, :scraped_at) RETURNING id"
        ),
        {"title": title, "scraped_at": "2026-05-08T00:00:00Z"},
    )
    return int(result.scalar_one())


async def _insert_employer_account(
    session: AsyncSession,
    *,
    name: str,
    domain: str = "example.com",
    verification_status: str = "pending",
    source_trust_tier: str = "unknown",
) -> int:
    """Insert an employer_accounts row and return its id."""
    result = await session.execute(
        text(
            "INSERT INTO employer_accounts "
            "(name, domain, verification_status, source_trust_tier, "
            "created_at) "
            "VALUES (:name, :domain, :status, :tier, :created_at) "
            "RETURNING id"
        ),
        {
            "name": name,
            "domain": domain,
            "status": verification_status,
            "tier": source_trust_tier,
            "created_at": "2026-05-08T00:00:00Z",
        },
    )
    return int(result.scalar_one())


# ---------------------------------------------------------------------------
# Table presence
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_employer_accounts_table_exists(session_factory):
    """Empty SELECT proves the employer_accounts table is present."""
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT id, name, domain, verification_status, "
                "verified_at, verified_by_account_id, retired_at, "
                "source_trust_tier, created_at FROM employer_accounts"
            )
        )
        assert result.first() is None


@pytest.mark.anyio
async def test_listing_claims_table_exists(session_factory):
    """Empty SELECT proves the listing_claims table is present."""
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT id, claim_token_hash, listing_id, "
                "employer_account_id, claimant_email, "
                "claimant_account_id, expires_at, used_at, created_at "
                "FROM listing_claims"
            )
        )
        assert result.first() is None


@pytest.mark.anyio
async def test_listing_verifications_table_exists(session_factory):
    """Empty SELECT proves the listing_verifications table is present."""
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT listing_id, employer_account_id, "
                "verification_tier, intake_completed_at, intake_json, "
                "verified_at, created_at FROM listing_verifications"
            )
        )
        assert result.first() is None


@pytest.mark.anyio
async def test_listing_reputation_events_table_exists(session_factory):
    """Empty SELECT proves the listing_reputation_events table is present."""
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT id, listing_id, event_kind, session_id, "
                "occurred_at, recorded_by, notes "
                "FROM listing_reputation_events"
            )
        )
        assert result.first() is None


# ---------------------------------------------------------------------------
# ENUM CHECK constraints
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_employer_accounts_status_check_rejects_invalid(
    session_factory,
):
    """employer_accounts.verification_status CHECK rejects bad values."""
    async with session_factory() as session:
        with pytest.raises(Exception):
            await _insert_employer_account(
                session, name="bad-status", verification_status="bogus"
            )


@pytest.mark.anyio
async def test_employer_accounts_source_trust_tier_check_rejects_invalid(
    session_factory,
):
    """employer_accounts.source_trust_tier CHECK rejects bad values."""
    async with session_factory() as session:
        with pytest.raises(Exception):
            await _insert_employer_account(
                session, name="bad-tier", source_trust_tier="megacorp"
            )


@pytest.mark.anyio
async def test_employer_accounts_status_accepts_all_enum_values(
    session_factory,
):
    """Every value in VERIFICATION_STATUSES is accepted by the CHECK."""
    async with session_factory() as session:
        for i, status in enumerate(VERIFICATION_STATUSES):
            await _insert_employer_account(
                session, name=f"co-{i}", verification_status=status
            )


@pytest.mark.anyio
async def test_employer_accounts_source_trust_tier_accepts_all(
    session_factory,
):
    """Every value in SOURCE_TRUST_TIERS is accepted by the CHECK."""
    async with session_factory() as session:
        for i, tier in enumerate(SOURCE_TRUST_TIERS):
            await _insert_employer_account(
                session, name=f"src-{i}", source_trust_tier=tier
            )


@pytest.mark.anyio
async def test_listing_verifications_tier_check_rejects_invalid(
    session_factory,
):
    """listing_verifications.verification_tier CHECK rejects bad values."""
    async with session_factory() as session:
        listing_id = await _make_listing(session, title="vt-listing")
        emp_id = await _insert_employer_account(session, name="vt-co")
        with pytest.raises(Exception):
            await session.execute(
                text(
                    "INSERT INTO listing_verifications "
                    "(listing_id, employer_account_id, verification_tier, "
                    "verified_at, created_at) "
                    "VALUES (:lid, :eid, 'bogus_tier', :ts, :ts)"
                ),
                {
                    "lid": listing_id,
                    "eid": emp_id,
                    "ts": "2026-05-08T00:00:00Z",
                },
            )


@pytest.mark.anyio
async def test_listing_reputation_events_kind_check_rejects_invalid(
    session_factory,
):
    """listing_reputation_events.event_kind CHECK rejects bad values."""
    async with session_factory() as session:
        listing_id = await _make_listing(session, title="ek-listing")
        with pytest.raises(Exception):
            await session.execute(
                text(
                    "INSERT INTO listing_reputation_events "
                    "(listing_id, event_kind, occurred_at) "
                    "VALUES (:lid, 'not_an_event', :ts)"
                ),
                {"lid": listing_id, "ts": "2026-05-08T00:00:00Z"},
            )


# ---------------------------------------------------------------------------
# UNIQUE constraints
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_listing_verifications_unique_listing_id(session_factory):
    """UNIQUE(listing_id) blocks two verifications for the same listing."""
    async with session_factory() as session:
        listing_id = await _make_listing(session, title="uv-listing")
        emp_id = await _insert_employer_account(session, name="uv-co")
        await session.execute(
            text(
                "INSERT INTO listing_verifications "
                "(listing_id, employer_account_id, verification_tier, "
                "verified_at, created_at) "
                "VALUES (:lid, :eid, 'source_trust', :ts, :ts)"
            ),
            {
                "lid": listing_id,
                "eid": emp_id,
                "ts": "2026-05-08T00:00:00Z",
            },
        )
        with pytest.raises(Exception):
            await session.execute(
                text(
                    "INSERT INTO listing_verifications "
                    "(listing_id, employer_account_id, verification_tier, "
                    "verified_at, created_at) "
                    "VALUES (:lid, :eid, 'claim_verified', :ts, :ts)"
                ),
                {
                    "lid": listing_id,
                    "eid": emp_id,
                    "ts": "2026-05-08T00:00:00Z",
                },
            )


@pytest.mark.anyio
async def test_employer_accounts_name_is_unique(session_factory):
    """employer_accounts.name UNIQUE blocks duplicate names."""
    async with session_factory() as session:
        await _insert_employer_account(session, name="dupe-co")
        with pytest.raises(Exception):
            await _insert_employer_account(session, name="dupe-co")


@pytest.mark.anyio
async def test_listing_claims_token_hash_is_unique(session_factory):
    """listing_claims.claim_token_hash UNIQUE blocks duplicate tokens."""
    async with session_factory() as session:
        listing_id = await _make_listing(session, title="ct-listing")
        account_id = await _make_account(session, "ct@example.com")
        await session.execute(
            text(
                "INSERT INTO listing_claims "
                "(claim_token_hash, listing_id, claimant_email, "
                "claimant_account_id, expires_at, created_at) "
                "VALUES (:h, :lid, :email, :aid, :ts, :ts)"
            ),
            {
                "h": "deadbeef",
                "lid": listing_id,
                "email": "ct@example.com",
                "aid": account_id,
                "ts": "2026-05-08T00:00:00Z",
            },
        )
        with pytest.raises(Exception):
            await session.execute(
                text(
                    "INSERT INTO listing_claims "
                    "(claim_token_hash, listing_id, claimant_email, "
                    "claimant_account_id, expires_at, created_at) "
                    "VALUES (:h, :lid, :email, :aid, :ts, :ts)"
                ),
                {
                    "h": "deadbeef",
                    "lid": listing_id,
                    "email": "ct@example.com",
                    "aid": account_id,
                    "ts": "2026-05-08T00:00:00Z",
                },
            )


# ---------------------------------------------------------------------------
# Reputation event index — present on (listing_id, occurred_at)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_listing_reputation_events_index_present(session_factory):
    """Index on (listing_id, occurred_at) for the rolling-window query.

    Verified by inspecting sqlite_master so we don't depend on EXPLAIN
    QUERY PLAN's wording across sqlite versions.
    """
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' "
                "AND tbl_name='listing_reputation_events'"
            )
        )
        names = [row[0] for row in result.fetchall()]
        assert any(
            "listing_id" in n and "occurred_at" in n for n in names
        ), f"expected an index on (listing_id, occurred_at), got {names!r}"


# ---------------------------------------------------------------------------
# Enum-tuple coverage (single source of truth)
# ---------------------------------------------------------------------------


def test_enum_tuples_match_spec():
    """ENUM tuples expose the canonical set of values for the app layer."""
    assert VERIFICATION_STATUSES == (
        "pending",
        "claimed",
        "admin_review",
        "verified",
        "retired",
    )
    assert SOURCE_TRUST_TIERS == (
        "unknown",
        "brightdata",
        "honestjobs",
        "twc",
        "manual",
    )
    assert VERIFICATION_TIERS == (
        "source_trust",
        "claim_verified",
        "admin_reviewed",
    )
    assert EVENT_KINDS == (
        "response_received",
        "withdrawn",
        "placed",
        "ghosted",
    )
