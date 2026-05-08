"""Async CRUD surface for the listing claim + verification flow (T24.2).

Thin ``text()``-based helpers operating on an :class:`AsyncSession`.
Sole writer/reader for the ``listing_claims`` and
``listing_verifications`` tables.

Claim flow (anti-oracle)
------------------------
The mint side returns a raw token (handed to the email integration once
and dropped); only the SHA-256 hash lands on disk. The validate side
(:func:`find_unused_claim_by_hash`) returns ``None`` for any failure
mode — not-found, expired, used — so the route layer can answer with a
uniform 401 and not leak token-state via timing or status code.

Verification idempotency
------------------------
``UNIQUE(listing_id)`` on ``listing_verifications`` means one verification
per listing. :func:`create_verification` wraps that with a friendly
state-machine guard: same-employer re-claim is silent (idempotent),
different-employer collision raises ``ValueError`` (translatable to 409
by the route layer).
"""

from __future__ import annotations

import secrets
from datetime import timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core._listings_verification_internals import (
    assert_claim_usable,
    assert_no_other_owner,
    extract_domain_from_email,
    hash_claim_token,
    normalize_email,
    utcnow,
    utcnow_iso,
)
from app.core.listings_verification_schema import VERIFICATION_TIERS

#: Default magic-link claim lifetime — short by design (T24.2 spec).
_CLAIM_TTL = timedelta(minutes=15)


# ---------------------------------------------------------------------------
# Claim flow (mint / find / mark-used)
# ---------------------------------------------------------------------------


async def mint_listing_claim_token(
    session: AsyncSession,
    *,
    listing_id: int,
    claimant_email: str,
    claimant_account_id: int | None,
) -> tuple[str, int]:
    """Mint a single-use claim token tied to *listing_id*.

    Generates ~256 bits of entropy via :func:`secrets.token_urlsafe`,
    persists only the SHA-256 hash, and returns the raw token plus the
    new row's PK. The raw token MUST never land on disk — the route
    layer hands it to the email integration and then drops it. Default
    lifetime is 15 minutes (:data:`_CLAIM_TTL`).
    """
    raw_token = secrets.token_urlsafe(32)
    now = utcnow()
    result = await session.execute(
        text(
            "INSERT INTO listing_claims "
            "(claim_token_hash, listing_id, claimant_email, "
            "claimant_account_id, expires_at, created_at) "
            "VALUES (:h, :lid, :email, :aid, :exp, :now) RETURNING id"
        ),
        {
            "h": hash_claim_token(raw_token),
            "lid": listing_id,
            "email": normalize_email(claimant_email),
            "aid": claimant_account_id,
            "exp": (now + _CLAIM_TTL).isoformat(),
            "now": now.isoformat(),
        },
    )
    claim_id = int(result.scalar_one())
    await session.commit()
    return raw_token, claim_id


async def find_unused_claim_by_hash(
    session: AsyncSession, *, token_hash: str
) -> dict | None:
    """Return the claim row for a fresh hash, or None for any failure mode.

    All three failure modes — row missing, expired, used — collapse to
    ``None`` so the route layer answers with a uniform 401 and the token
    lifecycle isn't leaked via response shape.
    """
    result = await session.execute(
        text(
            "SELECT id, listing_id, employer_account_id, "
            "claimant_email, claimant_account_id, expires_at, "
            "used_at, created_at "
            "FROM listing_claims "
            "WHERE claim_token_hash = :h "
            "AND used_at IS NULL "
            "AND expires_at > :now"
        ),
        {"h": token_hash, "now": utcnow_iso()},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def mark_claim_used(session: AsyncSession, claim_id: int) -> None:
    """Stamp ``used_at = utcnow()`` on the claim row.

    Raises ``ValueError`` if the claim does not exist, is already used,
    or has expired — the route layer translates those to 401 / 409.
    """
    now_iso = utcnow_iso()
    await assert_claim_usable(session, claim_id, now_iso=now_iso)
    await session.execute(
        text("UPDATE listing_claims SET used_at = :now WHERE id = :id"),
        {"now": now_iso, "id": claim_id},
    )
    await session.commit()


# ---------------------------------------------------------------------------
# Verification CRUD
# ---------------------------------------------------------------------------

_INSERT_VERIFICATION_SQL = (
    "INSERT INTO listing_verifications "
    "(listing_id, employer_account_id, verification_tier, "
    "verified_at, created_at) "
    "VALUES (:lid, :eid, :tier, :ts, :ts)"
)


async def _insert_verification_row(
    session: AsyncSession,
    *,
    listing_id: int,
    employer_account_id: int,
    tier: str,
) -> None:
    """Insert one ``listing_verifications`` row + commit."""
    await session.execute(
        text(_INSERT_VERIFICATION_SQL),
        {
            "lid": listing_id,
            "eid": employer_account_id,
            "tier": tier,
            "ts": utcnow_iso(),
        },
    )
    await session.commit()


async def create_verification(
    session: AsyncSession,
    *,
    listing_id: int,
    employer_account_id: int,
    tier: str,
    verified_by: int,
) -> None:
    """Create one verification row for *listing_id*.

    Idempotent on (listing_id, employer_account_id) — re-claim by the
    SAME employer is a silent no-op. Re-claim by a DIFFERENT employer
    raises ``ValueError`` for the route layer to translate to 409.
    Tier is validated against :data:`VERIFICATION_TIERS` for a clean
    ``ValueError`` rather than an opaque CHECK violation.
    """
    if tier not in VERIFICATION_TIERS:
        raise ValueError(
            f"invalid tier {tier!r}; expected {VERIFICATION_TIERS}"
        )
    same_owner = await assert_no_other_owner(
        session,
        listing_id=listing_id,
        employer_account_id=employer_account_id,
    )
    if same_owner:
        return
    await _insert_verification_row(
        session,
        listing_id=listing_id,
        employer_account_id=employer_account_id,
        tier=tier,
    )


async def set_intake(
    session: AsyncSession, *, listing_id: int, intake_json: str
) -> None:
    """Store the freeform intake blob + stamp ``intake_completed_at``."""
    await session.execute(
        text(
            "UPDATE listing_verifications "
            "SET intake_json = :j, intake_completed_at = :ts "
            "WHERE listing_id = :lid"
        ),
        {"j": intake_json, "ts": utcnow_iso(), "lid": listing_id},
    )
    await session.commit()


async def get_verification_for_listing(
    session: AsyncSession, listing_id: int
) -> dict | None:
    """Full verification row including ``intake_json`` (employer-private)."""
    result = await session.execute(
        text(
            "SELECT id, listing_id, employer_account_id, "
            "verification_tier, intake_completed_at, intake_json, "
            "verified_at, created_at "
            "FROM listing_verifications WHERE listing_id = :lid"
        ),
        {"lid": listing_id},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_public_verification_summary(
    session: AsyncSession, listing_ids: list[int]
) -> dict[int, dict]:
    """Batched public read; ``intake_json`` deliberately EXCLUDED.

    Returns ``listing_id -> {verification_tier, employer_account_id,
    intake_complete: bool, verified_at}``. ``intake_complete`` is
    derived from ``intake_completed_at IS NOT NULL`` so consumers know
    intake is done without seeing freeform answers (which may carry PII
    or employer-confidential terms).
    """
    if not listing_ids:
        return {}
    placeholders = ", ".join(f":lid_{i}" for i in range(len(listing_ids)))
    binds = {f"lid_{i}": lid for i, lid in enumerate(listing_ids)}
    result = await session.execute(
        text(
            "SELECT listing_id, employer_account_id, verification_tier, "
            "intake_completed_at, verified_at "
            "FROM listing_verifications "
            f"WHERE listing_id IN ({placeholders})"
        ),
        binds,
    )
    summary: dict[int, dict] = {}
    for row in result:
        mp = row._mapping
        summary[int(mp["listing_id"])] = {
            "verification_tier": mp["verification_tier"],
            "employer_account_id": int(mp["employer_account_id"]),
            "intake_complete": mp["intake_completed_at"] is not None,
            "verified_at": mp["verified_at"],
        }
    return summary


__all__ = [
    "hash_claim_token",
    "extract_domain_from_email",
    "mint_listing_claim_token",
    "find_unused_claim_by_hash",
    "mark_claim_used",
    "create_verification",
    "set_intake",
    "get_verification_for_listing",
    "get_public_verification_summary",
]
