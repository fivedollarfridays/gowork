"""Role-based FastAPI dependencies (T22.6).

Exposes :func:`require_role` — a dependency factory that gates a
route on the requesting account holding a specific role. The
``account_id`` is resolved from the anonymous session (the same
``session_id`` cookie/header the rest of the app reads); an
unclaimed session is treated as anonymous and rejected with 403.

Usage::

    from fastapi import APIRouter, Depends
    from app.core.auth_roles import require_role

    router = APIRouter()

    @router.get("/admin/things")
    async def list_things(account=Depends(require_role("admin"))):
        ...

This sprint (S22) only the ``admin`` tier is wired into routes; the
other three roles (``case_manager``, ``sme_reviewer``,
``dao_reviewer``) ship to the reviewer dashboard in S23.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.queries_accounts import get_account_for_session
from app.core.queries_roles import account_has_role


def require_role(role: str):
    """Build a FastAPI dependency that requires *role* on the caller.

    Returns an async callable suitable for ``Depends(...)``. The
    callable raises :class:`HTTPException` 403 in two cases:

    * ``"Authentication required"`` — the session is anonymous (no
      row in ``account_sessions`` for the given ``session_id``).
    * ``"Insufficient permissions"`` — the account exists but lacks
      *role*.

    On success it returns the account dict so route handlers can
    consume it via ``account = Depends(require_role("admin"))``.
    """

    async def dependency(
        db: AsyncSession = Depends(get_db),
        session_id: str = "",
    ) -> dict:
        account = await get_account_for_session(db, session_id)
        if account is None:
            raise HTTPException(
                status_code=403, detail="Authentication required"
            )
        if not await account_has_role(db, int(account["id"]), role):
            raise HTTPException(
                status_code=403, detail="Insufficient permissions"
            )
        return account

    return dependency
