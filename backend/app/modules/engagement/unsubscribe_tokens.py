"""Signed single-use engagement-unsubscribe tokens (T12.21, S12b).

Session-scoped parallel of :mod:`app.modules.appointments.tokens`. Every
token embeds ``sid`` (session_id), ``act`` = "unsubscribe", ``exp``,
``iat``, and ``kid``, signed with ``UNSUBSCRIBE_TOKEN_SECRET`` (optional
``UNSUBSCRIBE_TOKEN_SECRET_OLD`` during rotation). The shared
``used_tokens`` table (m004) provides atomic replay protection — a
double-click on an unsubscribe link can only succeed once. The
``action`` column discriminates this namespace from appointment-action
tokens; SQLite's type affinity lets us store the session_id string in
the ``appointment_id INTEGER`` column without schema churn.

All failure modes raise :class:`TokenError` subclasses so the route
layer can funnel them into a single uniform 401 response (no
enumeration oracle).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

__all__ = [
    "TokenError",
    "TokenInvalid",
    "TokenExpired",
    "TokenAlreadyUsed",
    "sign",
    "verify",
]

_SECRET_ENV_VAR = "UNSUBSCRIBE_TOKEN_SECRET"
_SECRET_OLD_ENV_VAR = "UNSUBSCRIBE_TOKEN_SECRET_OLD"
_DEFAULT_TTL_SEC = 30 * 24 * 3600  # 30 days — unsubscribe links live in old emails
_ACTION = "unsubscribe"

# Kid values the verifier will route to a secret pool. Unknown kids are
# rejected outright — no fall-through to "try every active secret".
# Mirrors the T13.62 hardening in app.modules.appointments.tokens.
_KNOWN_KIDS = frozenset({"current", "old"})


class TokenError(ValueError):
    """Base class for unsubscribe-token failures.

    The route layer maps :class:`TokenInvalid` and :class:`TokenExpired`
    to a uniform 401 (no enumeration oracle); :class:`TokenAlreadyUsed`
    is treated as an idempotent success per CAN-SPAM Section 5(a)(4)
    (see ``app.routes.engagement._process_unsubscribe``).
    """


class TokenInvalid(TokenError):
    """Malformed token or signature does not match any active secret."""


class TokenExpired(TokenError):
    """Signature valid but ``exp`` is in the past."""


class TokenAlreadyUsed(TokenError):
    """Signature valid but the token has already been consumed (replay).

    The :attr:`session_id` attribute carries the *authenticated* session
    id (signature + ``exp`` were both verified before this exception was
    raised) so that idempotent callers — notably the unsubscribe route,
    which must satisfy CAN-SPAM by returning 200 on duplicate clicks —
    can return a successful response without a second decode pass.
    """

    def __init__(self, message: str, *, session_id: str | None = None) -> None:
        super().__init__(message)
        self.session_id = session_id


# ----------------------------------------------------------------- helpers

def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sha256_hex(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _active_secrets() -> list[tuple[str, str]]:
    """Return [(kid, secret), ...] — current first, then optional old."""
    out: list[tuple[str, str]] = []
    current = os.environ.get(_SECRET_ENV_VAR)
    if current:
        out.append(("current", current))
    old = os.environ.get(_SECRET_OLD_ENV_VAR)
    if old:
        out.append(("old", old))
    return out


def _compute_sig(secret: str, encoded_payload: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


# ----------------------------------------------------------------- sign

def sign(
    session_id: str,
    *,
    expires_in_sec: int = _DEFAULT_TTL_SEC,
    now: datetime | None = None,
) -> str:
    """Produce a URL-safe signed unsubscribe token for ``session_id``."""
    secrets = _active_secrets()
    if not secrets:
        raise RuntimeError(
            f"{_SECRET_ENV_VAR} must be set to sign unsubscribe tokens"
        )
    kid, secret = secrets[0]
    issued = now if now is not None else datetime.now(timezone.utc)
    iat = int(issued.timestamp())
    payload = {
        "sid": str(session_id),
        "act": _ACTION,
        "exp": iat + int(expires_in_sec),
        "iat": iat,
        "kid": kid,
    }
    encoded = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    sig = _compute_sig(secret, encoded)
    return f"{encoded}.{sig}"


# ----------------------------------------------------------------- verify

def verify(
    token: str,
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> str:
    """Validate + consume a token; return its session_id.

    Stages: shape + signature -> ``TokenInvalid``; ``exp`` ->
    ``TokenExpired``; atomic INSERT into ``used_tokens`` ->
    ``TokenAlreadyUsed``.
    """
    payload = _decode_and_verify_signature(token)
    _check_expiry(payload, now)
    session_id = str(payload.get("sid") or "")
    if not session_id:
        raise TokenInvalid("payload missing sid")
    _consume_or_raise(
        token=token, session_id=session_id, db_path=db_path,
        now=now if now is not None else datetime.now(timezone.utc),
    )
    return session_id


# ----------------------------------------------------------------- stages

def _decode_and_verify_signature(token: str) -> dict:
    """Return the decoded payload dict or raise TokenInvalid."""
    if not token or not isinstance(token, str) or token.count(".") != 1:
        raise TokenInvalid("token must be <encoded>.<signature>")
    encoded, provided_sig = token.split(".", 1)
    try:
        raw = _b64url_decode(encoded)
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise TokenInvalid("payload is not valid base64url JSON") from exc
    if not isinstance(payload, dict):
        raise TokenInvalid("payload must be a JSON object")
    if payload.get("act") != _ACTION:
        raise TokenInvalid("wrong action for unsubscribe scope")
    payload_kid = payload.get("kid", "current")
    if payload_kid not in _KNOWN_KIDS:
        raise TokenInvalid("unknown kid")
    active = _active_secrets()
    candidates = (
        [(k, s) for k, s in active if k == "old"]
        if payload_kid == "old"
        else active
    )
    for _kid, secret in candidates:
        expected_sig = _compute_sig(secret, encoded)
        if hmac.compare_digest(expected_sig, provided_sig):
            return payload
    raise TokenInvalid("signature does not match any active secret")


def _check_expiry(payload: dict, now: datetime | None) -> None:
    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise TokenInvalid("payload missing integer exp")
    cutoff = int(
        (now if now is not None else datetime.now(timezone.utc)).timestamp()
    )
    if exp < cutoff:
        raise TokenExpired(f"token expired at {exp}")


def _consume_or_raise(
    *,
    token: str,
    session_id: str,
    db_path: str | Path,
    now: datetime,
) -> None:
    """INSERT OR IGNORE into used_tokens; raise if row already existed.

    session_id is stored in the ``appointment_id`` column — SQLite's
    type affinity (not strict types) allows the string write, and the
    ``action = 'unsubscribe'`` discriminator keeps this namespace
    separate from the appointment-token namespace.
    """
    token_hash = _sha256_hex(token)
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO used_tokens "
            "(token_hash, used_at, action, appointment_id) "
            "VALUES (?, ?, ?, ?)",
            (token_hash, now.isoformat(), _ACTION, session_id),
        )
        conn.commit()
        if cursor.rowcount != 1:
            raise TokenAlreadyUsed(
                "token already consumed", session_id=session_id,
            )
    finally:
        conn.close()
