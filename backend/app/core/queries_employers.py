"""Async CRUD surface for ``employer_accounts`` (T24.2).

Thin ``text()``-based helpers operating on an :class:`AsyncSession`,
following the :mod:`app.core.queries_accounts` pattern. Sole writer
to the ``employer_accounts`` table; read paths join into
``listing_verifications`` + ``job_listings`` for the admin queue.

Domain normalization
--------------------
Domains are lowercased + stripped on insert AND on lookup so the
``UNIQUE``-style "one employer per domain" semantic holds case-
insensitively. Email-like inputs are not parsed here — that's the
caller's responsibility (see ``extract_domain_from_email`` in the
verification queries module).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _utcnow_iso() -> str:
    """UTC timestamp string for ``created_at`` columns (mirrors siblings)."""
    return datetime.now(timezone.utc).isoformat()


def _normalize_domain(domain: str | None) -> str | None:
    """Lowercase + strip a domain so UNIQUE-style lookups are CI."""
    if domain is None:
        return None
    return domain.strip().lower()


async def create_employer_account(
    session: AsyncSession, *, name: str, domain: str | None
) -> int:
    """Insert one ``employer_accounts`` row, return its new primary key.

    ``name`` is UNIQUE — duplicates surface as the dialect's
    ``IntegrityError`` for the route layer to translate to 409.
    ``domain`` is normalized to lowercase + stripped before persist
    so case variants don't shard one company across rows.
    """
    normalized = _normalize_domain(domain)
    result = await session.execute(
        text(
            "INSERT INTO employer_accounts "
            "(name, domain, created_at) "
            "VALUES (:name, :domain, :ts) RETURNING id"
        ),
        {"name": name, "domain": normalized, "ts": _utcnow_iso()},
    )
    new_id = int(result.scalar_one())
    await session.commit()
    return new_id


async def get_employer_by_id(
    session: AsyncSession, employer_id: int
) -> dict | None:
    """Fetch the employer row matching *employer_id* or None."""
    result = await session.execute(
        text("SELECT * FROM employer_accounts WHERE id = :id"),
        {"id": employer_id},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_employer_by_domain(
    session: AsyncSession, domain: str
) -> dict | None:
    """Fetch the employer row matching *domain* (case-insensitive) or None."""
    normalized = _normalize_domain(domain)
    result = await session.execute(
        text("SELECT * FROM employer_accounts WHERE domain = :d"),
        {"d": normalized},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def list_pending_admin_review(
    session: AsyncSession,
) -> list[dict]:
    """Claims whose listing's verification_tier is ``admin_reviewed``.

    Joins ``listing_claims`` to ``listing_verifications`` (via
    listing_id), ``employer_accounts``, and ``job_listings`` so the
    admin queue UI gets the claim id, claimant email, employer name,
    and listing title in one round-trip. The queue is keyed by
    ``listing_claims.id`` (the per-attempt PK) so the front-end's
    detail/approve/reject routes can use ``claim_id`` consistently.
    """
    result = await session.execute(
        text(
            "SELECT c.id AS claim_id, "
            "c.claimant_email, "
            "c.created_at AS claim_created_at, "
            "v.id AS verification_id, "
            "v.listing_id, "
            "v.employer_account_id, "
            "v.verification_tier, "
            "v.intake_completed_at, "
            "v.created_at AS verification_created_at, "
            "e.name AS employer_name, "
            "e.domain AS employer_domain, "
            "j.title AS listing_title "
            "FROM listing_claims c "
            "JOIN listing_verifications v ON v.listing_id = c.listing_id "
            "JOIN employer_accounts e ON e.id = v.employer_account_id "
            "JOIN job_listings j ON j.id = v.listing_id "
            "WHERE v.verification_tier = 'admin_reviewed' "
            "ORDER BY c.created_at"
        )
    )
    return [dict(row._mapping) for row in result]


async def get_claim_detail(
    session: AsyncSession, claim_id: int
) -> dict | None:
    """Full admin-review payload for one ``listing_claims`` row.

    LEFT JOINs the verification + intake side: a claim can exist
    without a verification (rare — the T24.4 verify path always writes
    one) but the detail surface must still describe the claim shape.
    Returns ``None`` when the claim id does not exist.
    """
    result = await session.execute(
        text(
            "SELECT c.id AS claim_id, "
            "c.claimant_email, "
            "c.listing_id, "
            "c.created_at AS claim_created_at, "
            "c.expires_at, "
            "c.used_at, "
            "j.title AS listing_title, "
            "j.company AS listing_company, "
            "v.id AS verification_id, "
            "v.employer_account_id, "
            "v.verification_tier, "
            "v.intake_json, "
            "v.intake_completed_at, "
            "v.verified_at, "
            "e.name AS employer_name, "
            "e.domain AS employer_domain, "
            "e.verification_status AS employer_status "
            "FROM listing_claims c "
            "JOIN job_listings j ON j.id = c.listing_id "
            "LEFT JOIN listing_verifications v ON v.listing_id = c.listing_id "
            "LEFT JOIN employer_accounts e ON e.id = v.employer_account_id "
            "WHERE c.id = :id"
        ),
        {"id": claim_id},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def approve_admin_review(
    session: AsyncSession, claim_id: int
) -> dict | None:
    """Promote the claim's employer to ``verified`` + refresh verified_at.

    Returns ``{claim_id, employer_account_id, verification_status,
    verified_at}`` on success. Verification tier stays at
    ``admin_reviewed`` — that's the canonical post-admin-approval
    label. Returns ``None`` when the claim id does not exist.
    """
    detail = await get_claim_detail(session, claim_id)
    if detail is None:
        return None
    employer_id = detail.get("employer_account_id")
    listing_id = detail["listing_id"]
    now = _utcnow_iso()
    if employer_id is not None:
        await session.execute(
            text(
                "UPDATE employer_accounts "
                "SET verification_status = 'verified', "
                "verified_at = :ts WHERE id = :id"
            ),
            {"id": int(employer_id), "ts": now},
        )
        await session.execute(
            text(
                "UPDATE listing_verifications "
                "SET verified_at = :ts WHERE listing_id = :lid"
            ),
            {"ts": now, "lid": int(listing_id)},
        )
    await session.commit()
    return {
        "claim_id": claim_id,
        "employer_account_id": employer_id,
        "verification_status": "verified",
        "verified_at": now,
    }


async def reject_admin_review(
    session: AsyncSession, claim_id: int
) -> bool:
    """Tear down the claim + verification; retire the employer.

    Returns ``True`` on success, ``False`` when the claim id does not
    exist. Side-effects:

    * delete the ``listing_claims`` row,
    * delete the matching ``listing_verifications`` row (if present),
    * set the employer's ``verification_status`` to ``retired``.
    """
    detail = await get_claim_detail(session, claim_id)
    if detail is None:
        return False
    listing_id = int(detail["listing_id"])
    employer_id = detail.get("employer_account_id")
    await session.execute(
        text("DELETE FROM listing_verifications WHERE listing_id = :lid"),
        {"lid": listing_id},
    )
    await session.execute(
        text("DELETE FROM listing_claims WHERE id = :id"),
        {"id": claim_id},
    )
    if employer_id is not None:
        await session.execute(
            text(
                "UPDATE employer_accounts "
                "SET verification_status = 'retired' WHERE id = :id"
            ),
            {"id": int(employer_id)},
        )
    await session.commit()
    return True


__all__ = [
    "create_employer_account",
    "get_employer_by_id",
    "get_employer_by_domain",
    "list_pending_admin_review",
    "get_claim_detail",
    "approve_admin_review",
    "reject_admin_review",
]
