"""Role-based FastAPI dependencies (T22.6).

Exposes :func:`require_role` — a dependency factory that gates a
route on the requesting account holding a specific role. The
``account_id`` is resolved from the signed ``gw_account`` cookie set
by ``GET /api/auth/claim``; an unsigned/missing cookie is treated as
anonymous and rejected with 403.

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

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.queries_accounts import get_account_by_id
from app.core.queries_roles import account_has_role


# ``SESSION_COOKIE_NAME`` is imported lazily inside the dependency
# closures below — top-level import of ``app.routes._auth_claim_helpers``
# triggers ``app.routes/__init__.py``, which (S23) registers the
# reviewer / drafter routers, which in turn import this module. The
# resulting circular import is broken by deferring resolution to
# request time. The constant value is duplicated here for the
# ``Cookie(alias=...)`` default so the dependency signature is still
# resolvable at import time.
_SESSION_COOKIE_ALIAS = "gw_account"


async def _resolve_authenticated_account(
    db: AsyncSession, gw_account: str | None,
) -> dict:
    """Decode the cookie and load the account row, or raise 403.

    Shared by :func:`require_role` and :func:`any_of_roles` so the
    cookie -> account pipeline lives in exactly one place.
    """
    # Local import — see top-of-file note on the circular load order.
    from app.routes._auth_claim_helpers import verify_account_cookie

    account_id = verify_account_cookie(gw_account) if gw_account else None
    if account_id is None:
        raise HTTPException(
            status_code=403, detail="Authentication required"
        )
    account = await get_account_by_id(db, account_id)
    if account is None:
        raise HTTPException(
            status_code=403, detail="Authentication required"
        )
    return account


def require_role(role: str):
    """Build a FastAPI dependency that requires *role* on the caller.

    Returns an async callable suitable for ``Depends(...)``. The
    callable raises :class:`HTTPException` 403 in two cases:

    * ``"Authentication required"`` — no valid signed account cookie
      on the request (anonymous, missing, or tampered).
    * ``"Insufficient permissions"`` — the account exists but lacks
      *role*.

    On success it returns the account dict so route handlers can
    consume it via ``account = Depends(require_role("admin"))``.

    Security note: the ``gw_account`` cookie is read via FastAPI's
    ``Cookie(...)`` source so it cannot be supplied as a query string
    parameter. Earlier drafts used a bare ``session_id: str = ""``
    which FastAPI binds as a query param — that allowed an attacker
    to attach ``?gw_account=<victim>`` and impersonate. Cookie source
    closes that hole.
    """

    async def dependency(
        db: AsyncSession = Depends(get_db),
        gw_account: str | None = Cookie(default=None, alias=_SESSION_COOKIE_ALIAS),
    ) -> dict:
        account = await _resolve_authenticated_account(db, gw_account)
        if not await account_has_role(db, account["id"], role):
            raise HTTPException(
                status_code=403, detail="Insufficient permissions"
            )
        return account

    return dependency


def any_of_roles(*roles: str):
    """Build a FastAPI dependency that requires ANY of *roles* on the caller.

    Mirrors :func:`require_role` but accepts an OR-list — the gate
    passes as soon as the caller's account holds any of the supplied
    roles. Useful for routes (T23.3 drafter, T23.4 reviewer queue)
    where multiple distinct roles share an action.

    The same 403 surface as :func:`require_role`:

    * ``"Authentication required"`` — no valid signed account cookie.
    * ``"Insufficient permissions"`` — account exists but holds none
      of *roles*.

    Returns the account dict on success.
    """
    if not roles:
        raise ValueError("any_of_roles requires at least one role")

    async def dependency(
        db: AsyncSession = Depends(get_db),
        gw_account: str | None = Cookie(default=None, alias=_SESSION_COOKIE_ALIAS),
    ) -> dict:
        account = await _resolve_authenticated_account(db, gw_account)
        for role in roles:
            if await account_has_role(db, account["id"], role):
                return account
        raise HTTPException(
            status_code=403, detail="Insufficient permissions"
        )

    return dependency
