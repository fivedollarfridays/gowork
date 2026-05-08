"""Internal helpers for :mod:`app.core.queries_listings_verification` (T24.2).

Split out so the public CRUD module stays under the per-file size +
function-count budgets. NOT part of the public surface — every helper
here is consumed only by ``queries_listings_verification``.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def utcnow() -> datetime:
    """Aware UTC ``datetime`` (single source for all timestamp paths)."""
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    """ISO-8601 UTC timestamp string for ``*_at`` columns."""
    return utcnow().isoformat()


def normalize_email(email: str) -> str:
    """Lowercase + strip an email — claimant lookup must be CI."""
    return email.strip().lower()


def hash_claim_token(raw_token: str) -> str:
    """SHA-256 hex digest of *raw_token* — the form persisted on disk.

    Mirror of :func:`app.core.queries_credentials.hash_token` but lives
    here so the verification module is self-contained.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def extract_domain_from_email(email: str) -> str | None:
    """``alice@acmehiring.com`` → ``acmehiring.com``; None on malformed."""
    parts = normalize_email(email).split("@")
    if len(parts) != 2 or not parts[1]:
        return None
    return parts[1]


async def existing_verification_owner(
    session: AsyncSession, listing_id: int
) -> int | None:
    """Return the employer_account_id verifying *listing_id*, else None."""
    result = await session.execute(
        text(
            "SELECT employer_account_id FROM listing_verifications "
            "WHERE listing_id = :lid"
        ),
        {"lid": listing_id},
    )
    row = result.first()
    return int(row._mapping["employer_account_id"]) if row else None


async def assert_no_other_owner(
    session: AsyncSession,
    *,
    listing_id: int,
    employer_account_id: int,
) -> bool:
    """Guard against re-claim by a different employer.

    Returns ``True`` if the listing is already verified by the SAME
    employer (caller should silently no-op). Returns ``False`` if the
    listing is unclaimed (caller should INSERT). Raises ``ValueError``
    if the listing is verified by a *different* employer (translatable
    to 409 by the route layer).
    """
    existing = await existing_verification_owner(session, listing_id)
    if existing is None:
        return False
    if existing == employer_account_id:
        return True
    raise ValueError(
        f"listing {listing_id} already verified by employer "
        f"{existing}; cannot re-claim under {employer_account_id}"
    )


async def assert_claim_usable(
    session: AsyncSession, claim_id: int, *, now_iso: str
) -> None:
    """Raise ValueError unless claim is fresh + unused.

    Pulled out of :func:`mark_claim_used` so the public function stays
    inside the function-length budget.
    """
    result = await session.execute(
        text(
            "SELECT used_at, expires_at FROM listing_claims "
            "WHERE id = :id"
        ),
        {"id": claim_id},
    )
    row = result.first()
    if row is None:
        raise ValueError(f"claim {claim_id} does not exist")
    used_at = row._mapping["used_at"]
    expires_at = row._mapping["expires_at"]
    if used_at is not None:
        raise ValueError(f"claim {claim_id} already used at {used_at}")
    if expires_at <= now_iso:
        raise ValueError(f"claim {claim_id} expired at {expires_at}")


__all__ = [
    "utcnow",
    "utcnow_iso",
    "normalize_email",
    "hash_claim_token",
    "extract_domain_from_email",
    "existing_verification_owner",
    "assert_no_other_owner",
    "assert_claim_usable",
]
