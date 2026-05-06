"""Helpers backing ``GET /api/auth/claim`` (T22.8).

Lives next to ``app.routes.auth`` so the claim handler can stay inside
the architectural function-count budget on ``auth.py`` (12 functions).
The pieces here are:

* HMAC-signed account cookie (``gw_account``) — value format and the
  ``response.set_cookie`` wrapper with safe attribute defaults.
* The ``claim_session`` adapter that translates the underlying
  ``UNIQUE(session_id)`` IntegrityError into a boolean so the route
  layer can return a clean 409 without leaking ORM types.
* The two pre-baked uniform-401 / 409 ``Response`` builders, kept
  here so the byte-identical claim-failure body has exactly one
  source of truth (oracle-prevention).
"""

from __future__ import annotations

import hmac

from fastapi import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_accounts
from app.core.config import get_settings


SESSION_COOKIE_NAME = "gw_account"
_SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

# Pre-encoded JSON bodies. Bytes (not dicts) so every failure response
# is byte-identical — eliminates any whitespace / key-order oracle.
_INVALID_TOKEN_BODY = b'{"detail":"invalid_or_expired_token"}'
_CONFLICT_BODY = b'{"detail":"session_already_claimed"}'


def _sign_account_id(account_id: int) -> str:
    """HMAC-SHA256 hex digest of *account_id* under :data:`audit_hash_salt`.

    Reusing ``audit_hash_salt`` rather than introducing a new secret
    inherits the existing operational guarantees (production validator
    rejects the default value) without expanding the rotation surface.
    """
    salt = get_settings().audit_hash_salt.encode("utf-8")
    msg = str(account_id).encode("utf-8")
    return hmac.new(salt, msg, "sha256").hexdigest()


def build_account_cookie_value(account_id: int) -> str:
    """Format the cookie value as ``<account_id>.<hmac>``."""
    return f"{account_id}.{_sign_account_id(account_id)}"


def verify_account_cookie(value: str | None) -> int | None:
    """Return the account id encoded in *value* iff the HMAC validates.

    Counterpart to :func:`build_account_cookie_value` used by
    ``GET /api/auth/me`` (T22.11). Returns ``None`` for any of:

    * value is missing or empty,
    * value does not have the ``id.hmac`` shape,
    * id half is not a positive integer,
    * the HMAC half does not match the expected signature for the id.

    Use :func:`hmac.compare_digest` to keep the comparison
    constant-time so the validity check cannot be turned into a
    timing oracle on the secret.
    """
    if not value:
        return None
    parts = value.split(".", 1)
    if len(parts) != 2:
        return None
    raw_id, signature = parts
    try:
        account_id = int(raw_id)
    except ValueError:
        return None
    if account_id <= 0:
        return None
    expected = _sign_account_id(account_id)
    if not hmac.compare_digest(expected, signature):
        return None
    return account_id


def set_account_cookie(response: Response, account_id: int) -> None:
    """Attach the signed session cookie to *response* with safe defaults.

    Attributes:

    * ``HttpOnly`` — JS in the browser cannot read the cookie.
    * ``SameSite=Lax`` — sent on top-level navigations (the magic-link
      click is a top-level GET) but not on cross-site sub-requests.
    * ``Secure`` — only outside development so the dev server on plain
      http://localhost can still see the cookie.
    """
    secure = get_settings().environment != "development"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=build_account_cookie_value(account_id),
        max_age=_SESSION_COOKIE_MAX_AGE,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


async def try_claim_session(
    db: AsyncSession, *, account_id: int, session_id: str
) -> bool:
    """Bind *session_id* to *account_id*; return False on cross-account clash.

    Wraps :func:`queries_accounts.claim_session` so the route layer can
    translate the underlying ``UNIQUE(session_id)`` violation into a
    409 without importing ORM types. Returns True on success or
    idempotent re-claim by the same owner.
    """
    try:
        await queries_accounts.claim_session(db, account_id, session_id)
        return True
    except IntegrityError:
        await db.rollback()
        return False


def invalid_token_response() -> Response:
    """Uniform 401 used for every claim-failure mode (no lifecycle oracle)."""
    return Response(
        status_code=401,
        content=_INVALID_TOKEN_BODY,
        media_type="application/json",
    )


def session_conflict_response() -> Response:
    """409 returned when the session_id is owned by a different account."""
    return Response(
        status_code=409,
        content=_CONFLICT_BODY,
        media_type="application/json",
    )
