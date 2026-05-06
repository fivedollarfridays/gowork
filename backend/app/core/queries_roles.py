"""Async CRUD surface for the role layer (T22.6).

Mirrors the style of :mod:`app.core.queries_accounts` — thin
``text()``-based helpers operating on an :class:`AsyncSession`. These
are the only callers permitted to write to ``account_roles``; the
``require_role`` FastAPI dependency in :mod:`app.core.auth_roles`
layers on top of them.

Idempotency
-----------
* ``grant_role`` is idempotent: granting an already-held role is a
  noop (composite PK ``(account_id, role_name)`` makes the second
  insert redundant; we pre-check rather than swallow IntegrityError).
* ``revoke_role`` is idempotent: revoking a never-granted role is a
  noop.

Validation
----------
The SQL CHECK constraint (defined in :mod:`app.core.roles_schema`) is
the authoritative validator — invalid role strings raise the dialect's
``IntegrityError``. We surface that directly rather than re-validating
in Python, so the schema remains the single source of truth.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _utcnow_iso() -> str:
    """Return a stable UTC timestamp string for ``granted_at`` columns."""
    return datetime.now(timezone.utc).isoformat()


async def grant_role(
    session: AsyncSession, account_id: int, role_name: str
) -> None:
    """Grant *role_name* to *account_id* (idempotent).

    Pre-checks the composite PK so a second grant of the same role is
    a noop. Invalid role strings raise the underlying dialect's
    ``IntegrityError`` via the CHECK constraint defined in
    :mod:`app.core.roles_schema`.
    """
    existing = await session.execute(
        text(
            "SELECT 1 FROM account_roles "
            "WHERE account_id = :aid AND role_name = :role"
        ),
        {"aid": account_id, "role": role_name},
    )
    if existing.first() is not None:
        return  # idempotent re-grant
    await session.execute(
        text(
            "INSERT INTO account_roles (account_id, role_name, granted_at) "
            "VALUES (:aid, :role, :granted_at)"
        ),
        {"aid": account_id, "role": role_name, "granted_at": _utcnow_iso()},
    )
    await session.commit()


async def revoke_role(
    session: AsyncSession, account_id: int, role_name: str
) -> None:
    """Revoke *role_name* from *account_id* (idempotent).

    Deletes the row if present; if no row matches, completes silently.
    """
    await session.execute(
        text(
            "DELETE FROM account_roles "
            "WHERE account_id = :aid AND role_name = :role"
        ),
        {"aid": account_id, "role": role_name},
    )
    await session.commit()


async def list_roles_for_account(
    session: AsyncSession, account_id: int
) -> list[str]:
    """Return every role currently held by *account_id* (or [])."""
    result = await session.execute(
        text(
            "SELECT role_name FROM account_roles WHERE account_id = :aid"
        ),
        {"aid": account_id},
    )
    return [row._mapping["role_name"] for row in result]


async def account_has_role(
    session: AsyncSession, account_id: int, role_name: str
) -> bool:
    """Return True iff *account_id* currently holds *role_name*."""
    result = await session.execute(
        text(
            "SELECT 1 FROM account_roles "
            "WHERE account_id = :aid AND role_name = :role"
        ),
        {"aid": account_id, "role": role_name},
    )
    return result.first() is not None
