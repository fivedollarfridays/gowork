"""CRUD tests for :mod:`app.core.queries_employers` (T24.2).

Covers:

* ``create_employer_account`` — insert path + UNIQUE(name) collision.
* ``get_employer_by_id`` / ``get_employer_by_domain`` — lookup paths
  + None-on-miss + case-insensitive domain match.
* ``list_pending_admin_review`` — joins listing_verifications +
  employer_accounts + job_listings to surface admin-review queue.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core import queries_employers
from tests._listings_verification_test_fixtures import (
    make_account,
    make_listing,
    session_factory,  # noqa: F401  (re-exported for fixture wiring)
    verification_engine,  # noqa: F401
)


# ---------------------------------------------------------------------------
# create_employer_account
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_employer_account_returns_int_id(session_factory):
    """Successful insert returns the new primary key as an int."""
    async with session_factory() as session:
        new_id = await queries_employers.create_employer_account(
            session, name="Acme Hiring", domain="acmehiring.com"
        )
    assert isinstance(new_id, int)
    assert new_id > 0


@pytest.mark.anyio
async def test_create_employer_account_persists_row(session_factory):
    """Created row is readable via get_employer_by_id."""
    async with session_factory() as session:
        new_id = await queries_employers.create_employer_account(
            session, name="Acme Hiring", domain="acmehiring.com"
        )
    async with session_factory() as session:
        row = await queries_employers.get_employer_by_id(session, new_id)
    assert row is not None
    assert row["name"] == "Acme Hiring"
    assert row["domain"] == "acmehiring.com"
    assert row["verification_status"] == "pending"


@pytest.mark.anyio
async def test_create_employer_account_default_status_is_pending(
    session_factory,
):
    """Default verification_status is 'pending' (server_default applies)."""
    async with session_factory() as session:
        new_id = await queries_employers.create_employer_account(
            session, name="Default-status Co", domain="ds.com"
        )
        row = await queries_employers.get_employer_by_id(session, new_id)
    assert row is not None
    assert row["verification_status"] == "pending"
    assert row["source_trust_tier"] == "unknown"


@pytest.mark.anyio
async def test_create_employer_account_duplicate_name_raises(session_factory):
    """UNIQUE(name) collision surfaces as IntegrityError (translatable to 409)."""
    async with session_factory() as session:
        await queries_employers.create_employer_account(
            session, name="Dupe-co", domain="dupe.com"
        )
    async with session_factory() as session:
        with pytest.raises(Exception):
            await queries_employers.create_employer_account(
                session, name="Dupe-co", domain="other.com"
            )


@pytest.mark.anyio
async def test_create_employer_account_normalizes_domain(session_factory):
    """Domain is lowercased + stripped before persist."""
    async with session_factory() as session:
        new_id = await queries_employers.create_employer_account(
            session, name="Mixed-case", domain="  ACMEHiring.COM  "
        )
        row = await queries_employers.get_employer_by_id(session, new_id)
    assert row is not None
    assert row["domain"] == "acmehiring.com"


# ---------------------------------------------------------------------------
# get_employer_by_id / get_employer_by_domain
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_employer_by_id_missing_returns_none(session_factory):
    """Unknown id yields None rather than raising."""
    async with session_factory() as session:
        row = await queries_employers.get_employer_by_id(session, 9999)
    assert row is None


@pytest.mark.anyio
async def test_get_employer_by_domain_returns_match(session_factory):
    """Lookup by domain returns the right row."""
    async with session_factory() as session:
        await queries_employers.create_employer_account(
            session, name="By-domain Co", domain="bydomain.com"
        )
    async with session_factory() as session:
        row = await queries_employers.get_employer_by_domain(
            session, "bydomain.com"
        )
    assert row is not None
    assert row["name"] == "By-domain Co"


@pytest.mark.anyio
async def test_get_employer_by_domain_case_insensitive(session_factory):
    """Domain lookup is case-insensitive (lookup normalizes input)."""
    async with session_factory() as session:
        await queries_employers.create_employer_account(
            session, name="CI-co", domain="case.com"
        )
    async with session_factory() as session:
        row = await queries_employers.get_employer_by_domain(
            session, "CASE.COM"
        )
    assert row is not None
    assert row["name"] == "CI-co"


@pytest.mark.anyio
async def test_get_employer_by_domain_missing_returns_none(session_factory):
    """Unknown domain yields None."""
    async with session_factory() as session:
        row = await queries_employers.get_employer_by_domain(
            session, "nope.example"
        )
    assert row is None


# ---------------------------------------------------------------------------
# list_pending_admin_review
# ---------------------------------------------------------------------------


async def _seed_verification(
    session, *, listing_id: int, employer_id: int, tier: str
) -> None:
    """Helper: insert one listing_verifications row + a paired claim row.

    The admin-queue read (T24.9) inner-joins ``listing_claims`` so the
    queue is keyed by the per-attempt claim id (the URL the dashboard
    uses for the detail/approve/reject routes). Tests seed both rows
    via this helper so the join surfaces them.
    """
    await session.execute(
        text(
            "INSERT INTO listing_verifications "
            "(listing_id, employer_account_id, verification_tier, "
            "verified_at, created_at) "
            "VALUES (:lid, :eid, :tier, :ts, :ts)"
        ),
        {
            "lid": listing_id,
            "eid": employer_id,
            "tier": tier,
            "ts": "2026-05-08T00:00:00Z",
        },
    )
    await session.execute(
        text(
            "INSERT INTO listing_claims "
            "(claim_token_hash, listing_id, claimant_email, "
            "expires_at, created_at) "
            "VALUES (:h, :lid, :email, :exp, :ts)"
        ),
        {
            "h": f"hash-for-listing-{listing_id}",
            "lid": listing_id,
            "email": f"claimant-{listing_id}@example.com",
            "exp": "2099-01-01T00:00:00Z",
            "ts": "2026-05-08T00:00:00Z",
        },
    )
    await session.commit()


@pytest.mark.anyio
async def test_list_pending_admin_review_empty(session_factory):
    """No verifications yet → empty list."""
    async with session_factory() as session:
        rows = await queries_employers.list_pending_admin_review(session)
    assert rows == []


@pytest.mark.anyio
async def test_list_pending_admin_review_only_admin_review(session_factory):
    """Only verifications with tier='admin_reviewed' surface in queue.

    Treats ``admin_reviewed`` as the "needs admin attention" tier per
    the T24 spec — filter excludes ``source_trust`` and ``claim_verified``.
    """
    async with session_factory() as session:
        emp_id = await queries_employers.create_employer_account(
            session, name="Q-co", domain="q.com"
        )
        listing_admin = await make_listing(session, title="needs-admin")
        listing_other = await make_listing(session, title="claim-only")
        await _seed_verification(
            session,
            listing_id=listing_admin,
            employer_id=emp_id,
            tier="admin_reviewed",
        )
        await _seed_verification(
            session,
            listing_id=listing_other,
            employer_id=emp_id,
            tier="claim_verified",
        )
    async with session_factory() as session:
        rows = await queries_employers.list_pending_admin_review(session)
    assert len(rows) == 1
    assert rows[0]["listing_id"] == listing_admin


@pytest.mark.anyio
async def test_list_pending_admin_review_joins_employer_metadata(
    session_factory,
):
    """Returned rows include employer name + listing title from the join."""
    async with session_factory() as session:
        emp_id = await queries_employers.create_employer_account(
            session, name="Join-co", domain="j.com"
        )
        listing_id = await make_listing(session, title="Join-title")
        await _seed_verification(
            session,
            listing_id=listing_id,
            employer_id=emp_id,
            tier="admin_reviewed",
        )
    async with session_factory() as session:
        rows = await queries_employers.list_pending_admin_review(session)
    assert len(rows) == 1
    row = rows[0]
    assert row["employer_name"] == "Join-co"
    assert row["listing_title"] == "Join-title"


# Silence linter — fixture imports are intentional re-exports.
_unused = (verification_engine, make_account)
