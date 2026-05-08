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
    """Listings whose verification_tier is ``admin_reviewed``.

    Joins ``listing_verifications`` to ``employer_accounts`` and
    ``job_listings`` so the admin queue UI gets employer name + listing
    title in one round-trip. Treats ``admin_reviewed`` as the
    "needs admin attention" tier per the T24 spec.
    """
    result = await session.execute(
        text(
            "SELECT v.id AS verification_id, "
            "v.listing_id, "
            "v.employer_account_id, "
            "v.verification_tier, "
            "v.intake_completed_at, "
            "v.created_at AS verification_created_at, "
            "e.name AS employer_name, "
            "e.domain AS employer_domain, "
            "j.title AS listing_title "
            "FROM listing_verifications v "
            "JOIN employer_accounts e ON e.id = v.employer_account_id "
            "JOIN job_listings j ON j.id = v.listing_id "
            "WHERE v.verification_tier = 'admin_reviewed' "
            "ORDER BY v.created_at"
        )
    )
    return [dict(row._mapping) for row in result]


__all__ = [
    "create_employer_account",
    "get_employer_by_id",
    "get_employer_by_domain",
    "list_pending_admin_review",
]
