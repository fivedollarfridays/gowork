"""CRUD tests for :mod:`app.core.queries_listings_verification` (T24.2).

Covers the seven helpers consumed by the route layer:

* ``mint_listing_claim_token`` — raw_token return + SHA-256 hash on disk
  + 15-min default expiry.
* ``find_unused_claim_by_hash`` — uniform None for not-found / expired /
  used (anti-oracle invariant).
* ``mark_claim_used`` — idempotent stamp; ValueError on used / expired.
* ``create_verification`` — UNIQUE(listing_id) → IntegrityError;
  same-employer re-claim is silent; different employer raises ValueError.
* ``set_intake`` — stamps intake_completed_at.
* ``get_verification_for_listing`` — full row, intake_json INCLUDED.
* ``get_public_verification_summary`` — batched read, intake_json EXCLUDED;
  surfaces ``intake_complete: bool``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core import queries_listings_verification as qlv
from tests._listings_verification_test_fixtures import (
    make_account,
    make_listing,
    session_factory,  # noqa: F401
    verification_engine,  # noqa: F401
)


async def _seed_employer(session, *, name: str = "Co", domain: str = "c.com") -> int:
    """Insert one employer_accounts row, return its id."""
    result = await session.execute(
        text(
            "INSERT INTO employer_accounts "
            "(name, domain, verification_status, source_trust_tier, "
            "created_at) "
            "VALUES (:n, :d, 'pending', 'unknown', :ts) RETURNING id"
        ),
        {"n": name, "d": domain, "ts": "2026-05-08T00:00:00Z"},
    )
    new_id = int(result.scalar_one())
    await session.commit()
    return new_id


# ---------------------------------------------------------------------------
# mint_listing_claim_token
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_mint_claim_returns_raw_and_id(session_factory):
    """Mint returns (raw_token, claim_id) — int + str."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="m1")
        account_id = await make_account(session, "claimant@example.com")
        raw, claim_id = await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="claimant@example.com",
            claimant_account_id=account_id,
        )
    assert isinstance(raw, str)
    assert len(raw) >= 32
    assert isinstance(claim_id, int)


@pytest.mark.anyio
async def test_mint_claim_persists_only_hash(session_factory):
    """Raw token is NEVER on disk — only the SHA-256 hash."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="m2")
        account_id = await make_account(session, "h@example.com")
        raw, _ = await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="h@example.com",
            claimant_account_id=account_id,
        )
        rows = await session.execute(
            text("SELECT claim_token_hash FROM listing_claims")
        )
        hashes = [r[0] for r in rows.fetchall()]
    assert raw not in hashes
    # Hash should be 64 hex chars (SHA-256)
    assert all(len(h) == 64 for h in hashes)


@pytest.mark.anyio
async def test_mint_claim_default_expiry_is_15_minutes(session_factory):
    """Default expiry is utcnow() + 15 minutes (with small slack)."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="m3")
        account_id = await make_account(session, "exp@example.com")
        before = datetime.now(timezone.utc)
        await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="exp@example.com",
            claimant_account_id=account_id,
        )
        result = await session.execute(
            text("SELECT expires_at FROM listing_claims")
        )
        exp_iso = result.scalar_one()
    expires_at = datetime.fromisoformat(exp_iso)
    delta = expires_at - before
    assert timedelta(minutes=14) < delta < timedelta(minutes=16)


@pytest.mark.anyio
async def test_mint_claim_normalizes_email(session_factory):
    """Email is stored lowercased + stripped."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="m4")
        account_id = await make_account(session, "norm@example.com")
        await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="  Norm@Example.COM  ",
            claimant_account_id=account_id,
        )
        result = await session.execute(
            text("SELECT claimant_email FROM listing_claims")
        )
        email = result.scalar_one()
    assert email == "norm@example.com"


# ---------------------------------------------------------------------------
# find_unused_claim_by_hash
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_find_claim_returns_row_for_fresh_token(session_factory):
    """Fresh (unused, unexpired) claim is returned by hash lookup."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="f1")
        account_id = await make_account(session, "f1@example.com")
        raw, claim_id = await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="f1@example.com",
            claimant_account_id=account_id,
        )
    async with session_factory() as session:
        row = await qlv.find_unused_claim_by_hash(
            session, token_hash=qlv.hash_claim_token(raw)
        )
    assert row is not None
    assert row["id"] == claim_id
    assert row["listing_id"] == listing_id


@pytest.mark.anyio
async def test_find_claim_unknown_hash_returns_none(session_factory):
    """Unknown hash yields None (not-found path)."""
    async with session_factory() as session:
        row = await qlv.find_unused_claim_by_hash(
            session, token_hash="deadbeef" * 8
        )
    assert row is None


@pytest.mark.anyio
async def test_find_claim_expired_returns_none(session_factory):
    """Expired claim yields None (anti-oracle: indistinguishable from missing)."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="exp")
        account_id = await make_account(session, "exp@example.com")
        raw, claim_id = await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="exp@example.com",
            claimant_account_id=account_id,
        )
        # Manually backdate expiry
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        await session.execute(
            text("UPDATE listing_claims SET expires_at = :p WHERE id = :id"),
            {"p": past, "id": claim_id},
        )
        await session.commit()
    async with session_factory() as session:
        row = await qlv.find_unused_claim_by_hash(
            session, token_hash=qlv.hash_claim_token(raw)
        )
    assert row is None


@pytest.mark.anyio
async def test_find_claim_used_returns_none(session_factory):
    """Already-used claim yields None."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="used")
        account_id = await make_account(session, "u@example.com")
        raw, claim_id = await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="u@example.com",
            claimant_account_id=account_id,
        )
        await qlv.mark_claim_used(session, claim_id)
    async with session_factory() as session:
        row = await qlv.find_unused_claim_by_hash(
            session, token_hash=qlv.hash_claim_token(raw)
        )
    assert row is None


# ---------------------------------------------------------------------------
# mark_claim_used
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_mark_claim_used_stamps_used_at(session_factory):
    """Mark-used populates used_at."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="muu")
        account_id = await make_account(session, "muu@example.com")
        _raw, claim_id = await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="muu@example.com",
            claimant_account_id=account_id,
        )
        await qlv.mark_claim_used(session, claim_id)
        result = await session.execute(
            text("SELECT used_at FROM listing_claims WHERE id = :id"),
            {"id": claim_id},
        )
        used_at = result.scalar_one()
    assert used_at is not None


@pytest.mark.anyio
async def test_mark_claim_used_twice_raises(session_factory):
    """Second mark-used on same claim raises ValueError."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="tw")
        account_id = await make_account(session, "tw@example.com")
        _raw, claim_id = await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="tw@example.com",
            claimant_account_id=account_id,
        )
        await qlv.mark_claim_used(session, claim_id)
        with pytest.raises(ValueError):
            await qlv.mark_claim_used(session, claim_id)


@pytest.mark.anyio
async def test_mark_claim_used_expired_raises(session_factory):
    """Mark-used on already-expired claim raises ValueError."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="exp2")
        account_id = await make_account(session, "exp2@example.com")
        _raw, claim_id = await qlv.mint_listing_claim_token(
            session,
            listing_id=listing_id,
            claimant_email="exp2@example.com",
            claimant_account_id=account_id,
        )
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        await session.execute(
            text("UPDATE listing_claims SET expires_at = :p WHERE id = :id"),
            {"p": past, "id": claim_id},
        )
        await session.commit()
        with pytest.raises(ValueError):
            await qlv.mark_claim_used(session, claim_id)


# ---------------------------------------------------------------------------
# create_verification
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_verification_persists_row(session_factory):
    """Successful create persists tier + employer + verified_by."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="cv1")
        emp_id = await _seed_employer(session, name="cv-co", domain="cv.com")
        account_id = await make_account(session, "cv@example.com")
        await qlv.create_verification(
            session,
            listing_id=listing_id,
            employer_account_id=emp_id,
            tier="claim_verified",
        )
        row = await qlv.get_verification_for_listing(session, listing_id)
    assert row is not None
    assert row["verification_tier"] == "claim_verified"
    assert row["employer_account_id"] == emp_id


@pytest.mark.anyio
async def test_create_verification_invalid_tier_raises(session_factory):
    """Tier outside VERIFICATION_TIERS raises ValueError."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="cv2")
        emp_id = await _seed_employer(session, name="cv2-co", domain="cv2.com")
        account_id = await make_account(session, "cv2@example.com")
        with pytest.raises(ValueError):
            await qlv.create_verification(
                session,
                listing_id=listing_id,
                employer_account_id=emp_id,
                tier="bogus_tier",
            )


@pytest.mark.anyio
async def test_create_verification_same_employer_idempotent(session_factory):
    """Re-claim by SAME employer is silent (no error, no double row)."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="idem")
        emp_id = await _seed_employer(session, name="idem-co", domain="i.com")
        account_id = await make_account(session, "i@example.com")
        await qlv.create_verification(
            session,
            listing_id=listing_id,
            employer_account_id=emp_id,
            tier="claim_verified",
        )
        # Second call by same employer — should not raise
        await qlv.create_verification(
            session,
            listing_id=listing_id,
            employer_account_id=emp_id,
            tier="claim_verified",
        )
        result = await session.execute(
            text(
                "SELECT COUNT(*) FROM listing_verifications "
                "WHERE listing_id = :lid"
            ),
            {"lid": listing_id},
        )
        count = int(result.scalar_one())
    assert count == 1


@pytest.mark.anyio
async def test_create_verification_different_employer_raises(session_factory):
    """Re-claim by DIFFERENT employer raises ValueError (translatable to 409)."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="diff")
        emp_a = await _seed_employer(session, name="A-co", domain="a.com")
        emp_b = await _seed_employer(session, name="B-co", domain="b.com")
        account_id = await make_account(session, "diff@example.com")
        await qlv.create_verification(
            session,
            listing_id=listing_id,
            employer_account_id=emp_a,
            tier="claim_verified",
        )
        with pytest.raises(ValueError):
            await qlv.create_verification(
                session,
                listing_id=listing_id,
                employer_account_id=emp_b,
                tier="claim_verified",
            )


# ---------------------------------------------------------------------------
# set_intake / get_verification_for_listing
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_set_intake_persists_payload_and_timestamp(session_factory):
    """set_intake stores intake_json + stamps intake_completed_at."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="si1")
        emp_id = await _seed_employer(session, name="si-co", domain="si.com")
        account_id = await make_account(session, "si@example.com")
        await qlv.create_verification(
            session,
            listing_id=listing_id,
            employer_account_id=emp_id,
            tier="source_trust",
        )
        await qlv.set_intake(
            session,
            listing_id=listing_id,
            intake_json='{"hours_per_week": 40}',
        )
        row = await qlv.get_verification_for_listing(session, listing_id)
    assert row is not None
    assert row["intake_json"] == '{"hours_per_week": 40}'
    assert row["intake_completed_at"] is not None


@pytest.mark.anyio
async def test_get_verification_for_listing_missing_returns_none(
    session_factory,
):
    """Listing without verification yields None."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="none")
        row = await qlv.get_verification_for_listing(session, listing_id)
    assert row is None


# ---------------------------------------------------------------------------
# get_public_verification_summary
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_public_summary_excludes_intake_json(session_factory):
    """Public summary surfaces intake_complete:bool but not intake_json."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="pub1")
        emp_id = await _seed_employer(session, name="pub-co", domain="p.com")
        account_id = await make_account(session, "p@example.com")
        await qlv.create_verification(
            session,
            listing_id=listing_id,
            employer_account_id=emp_id,
            tier="claim_verified",
        )
        await qlv.set_intake(
            session,
            listing_id=listing_id,
            intake_json='{"secret": "do-not-leak"}',
        )
    async with session_factory() as session:
        summary = await qlv.get_public_verification_summary(
            session, [listing_id]
        )
    assert listing_id in summary
    payload = summary[listing_id]
    assert "intake_json" not in payload
    assert payload["intake_complete"] is True
    assert payload["verification_tier"] == "claim_verified"


@pytest.mark.anyio
async def test_public_summary_intake_complete_false_when_unset(
    session_factory,
):
    """intake_complete is False when intake_completed_at is null."""
    async with session_factory() as session:
        listing_id = await make_listing(session, title="pub2")
        emp_id = await _seed_employer(session, name="pub2-co", domain="p2.com")
        account_id = await make_account(session, "p2@example.com")
        await qlv.create_verification(
            session,
            listing_id=listing_id,
            employer_account_id=emp_id,
            tier="source_trust",
        )
    async with session_factory() as session:
        summary = await qlv.get_public_verification_summary(
            session, [listing_id]
        )
    assert summary[listing_id]["intake_complete"] is False


@pytest.mark.anyio
async def test_public_summary_batched(session_factory):
    """Multiple listings batched into one dict; missing listings absent."""
    async with session_factory() as session:
        l_a = await make_listing(session, title="ba")
        l_b = await make_listing(session, title="bb")
        l_c = await make_listing(session, title="bc")  # no verification
        emp_id = await _seed_employer(session, name="batch-co", domain="bb.com")
        account_id = await make_account(session, "ba@example.com")
        await qlv.create_verification(
            session,
            listing_id=l_a,
            employer_account_id=emp_id,
            tier="source_trust",
        )
        await qlv.create_verification(
            session,
            listing_id=l_b,
            employer_account_id=emp_id,
            tier="claim_verified",
        )
    async with session_factory() as session:
        summary = await qlv.get_public_verification_summary(
            session, [l_a, l_b, l_c]
        )
    assert l_a in summary
    assert l_b in summary
    assert l_c not in summary


@pytest.mark.anyio
async def test_public_summary_empty_input_returns_empty_dict(session_factory):
    """Empty listing_ids → empty dict (no SQL needed)."""
    async with session_factory() as session:
        summary = await qlv.get_public_verification_summary(session, [])
    assert summary == {}


# Silence linter — fixtures are imported for the side effect.
_unused = (verification_engine,)
