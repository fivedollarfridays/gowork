"""Async CRUD surface for the identity layer (T22.5).

Mirrors the style of :mod:`app.core.queries` — thin ``text()``-based
helpers operating on an :class:`AsyncSession`. The functions here are
the ONLY callers permitted to write to the ``accounts`` family of
tables; downstream features (magic-link issuance T22.7, claim flow
T22.8) layer on top of these primitives.

Magic-link credential CRUD lives in :mod:`app.core.queries_credentials`
and is re-exported from here so existing callers (route layer, tests)
keep their stable import path.

Anonymous-first invariant
-------------------------
None of these helpers mutate the legacy ``sessions`` table. An account
is bound to a session purely via the ``account_sessions`` link table;
``sessions.id`` rows continue to exist and to be served to anonymous
users without any account at all.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries_credentials import (
    find_unused_credential_by_hash,
    hash_token,
    mark_credential_used,
    mint_magic_link_credential,
)


def _utcnow_iso() -> str:
    """Return a stable UTC timestamp string for ``created_at`` columns."""
    return datetime.now(timezone.utc).isoformat()


def _normalize_email(email: str) -> str:
    """Lowercase + strip an email so UNIQUE lookups are case-insensitive."""
    return email.strip().lower()


async def create_account(session: AsyncSession, email: str) -> int:
    """Insert a new account row and return its primary key.

    Email is normalized (lowercased, trimmed) before insert so the
    UNIQUE constraint catches differently-cased duplicates. Raises
    the underlying dialect's ``IntegrityError`` on duplicate email.

    Portability note
    ----------------
    ``RETURNING id`` works on sqlite >= 3.35 and on every supported
    postgres version, so it is the simplest portable way to recover
    the new primary key.  ``text()``-bound INSERTs do not populate
    ``CursorResult.inserted_primary_key`` (that hook only fires for
    ``insert()`` Core constructs), hence the explicit RETURNING.
    """
    now = _utcnow_iso()
    normalized = _normalize_email(email)
    result = await session.execute(
        text(
            "INSERT INTO accounts (email, created_at, last_active_at) "
            "VALUES (:email, :created_at, :last_active_at) "
            "RETURNING id"
        ),
        {"email": normalized, "created_at": now, "last_active_at": now},
    )
    row = result.first()
    await session.commit()
    assert row is not None  # RETURNING always yields the inserted row
    return int(row[0])


async def get_account_by_email(
    session: AsyncSession, email: str
) -> dict | None:
    """Fetch the account row matching *email* (case-insensitive) or None."""
    normalized = _normalize_email(email)
    result = await session.execute(
        text("SELECT * FROM accounts WHERE email = :email"),
        {"email": normalized},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def claim_session(
    session: AsyncSession, account_id: int, session_id: str
) -> None:
    """Bind ``session_id`` to ``account_id`` via ``account_sessions``.

    Idempotent on the same ``(account_id, session_id)`` pair — we
    pre-check the link table and skip the INSERT when an identical
    row already exists. Raises the underlying dialect's
    ``IntegrityError`` when the session is already claimed by a
    *different* account (the ``UNIQUE(session_id)`` constraint).
    """
    existing = await session.execute(
        text(
            "SELECT account_id FROM account_sessions WHERE session_id = :sid"
        ),
        {"sid": session_id},
    )
    row = existing.first()
    if row is not None:
        if int(row._mapping["account_id"]) == account_id:
            return  # idempotent re-claim by the same owner
        # Different owner — let the UNIQUE(session_id) constraint
        # fire so the caller sees a real IntegrityError.
    now = _utcnow_iso()
    await session.execute(
        text(
            "INSERT INTO account_sessions "
            "(account_id, session_id, claimed_at) "
            "VALUES (:aid, :sid, :claimed_at)"
        ),
        {"aid": account_id, "sid": session_id, "claimed_at": now},
    )
    await session.commit()


async def list_sessions_for_account(
    session: AsyncSession, account_id: int
) -> list[str]:
    """Return every ``session_id`` claimed by *account_id*."""
    result = await session.execute(
        text(
            "SELECT session_id FROM account_sessions "
            "WHERE account_id = :aid"
        ),
        {"aid": account_id},
    )
    return [row._mapping["session_id"] for row in result]


async def get_account_for_session(
    session: AsyncSession, session_id: str
) -> dict | None:
    """Return the account row that claimed *session_id*, or None.

    Anonymous sessions (no row in ``account_sessions``) yield None —
    callers must treat that as the default "no account" path.
    """
    result = await session.execute(
        text(
            "SELECT a.* FROM accounts a "
            "JOIN account_sessions s ON s.account_id = a.id "
            "WHERE s.session_id = :sid"
        ),
        {"sid": session_id},
    )
    row = result.first()
    return dict(row._mapping) if row else None


# -------------------- Credential CRUD (T22.7 + T22.8) --------------------
# Re-exported from :mod:`app.core.queries_credentials` so the existing
# import path ``app.core.queries_accounts.<helper>`` keeps working
# while the credential-table CRUD lives in its own focused module.

__all__ = [
    "create_account",
    "get_account_by_email",
    "claim_session",
    "list_sessions_for_account",
    "get_account_for_session",
    "mint_magic_link_credential",
    "find_unused_credential_by_hash",
    "mark_credential_used",
    "hash_token",
]
