"""Signed single-use manage-appointment tokens (T12.10b).

HMAC-SHA256 signed tokens for email-CTA actions (cancel / reschedule /
view). Every token is stateless (payload carries aid, act, exp, iat,
kid), URL-safe (``base64url(json).base64url(sig)``), single-use (first
successful verify INSERTs ``sha256(token)`` into ``used_tokens``; the
UNIQUE constraint guarantees replays lose the race), and
rotation-ready (verify tries every active secret so tokens minted
before a rotation still validate until they expire).

``verify`` raises a ``TokenError`` subclass for every failure mode so
the HTTP layer can convert them all to a uniform 401 body (no
enumeration oracle). Subclasses exist for unit-test assertions;
routes must catch the base class. Signature compare uses
``hmac.compare_digest`` for constant-time equality. Replay protection
is atomic — a double-click cannot produce two writes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from app.core.token_kids import KNOWN_KIDS

__all__ = [
    "TokenAction",
    "TokenError",
    "TokenInvalid",
    "TokenExpired",
    "TokenActionMismatch",
    "TokenAlreadyUsed",
    "sign",
    "verify",
]

_SECRET_ENV_VAR = "APPOINTMENT_TOKEN_SECRET"
_SECRET_OLD_ENV_VAR = "APPOINTMENT_TOKEN_SECRET_OLD"
_DEFAULT_TTL_SEC = 7 * 24 * 3600  # 7 days

# Documented overlap window — see appointment-token-rotation.md §2.
# Equal to the default TTL: any pre-rotation token expires during the
# overlap, so retiring OLD on day 7 cannot strand a worker.
KEY_ROTATION_OVERLAP_DAYS = 7

# Kid values the verifier will route to a secret pool come from the
# shared `app.core.token_kids.KNOWN_KIDS` whitelist. Unknown kids are
# rejected outright — no fall-through to "try every active secret".


class TokenAction(str, Enum):
    """Actions a manage-link token authorises."""

    CANCEL = "cancel"
    RESCHEDULE = "reschedule"
    VIEW = "view"


class TokenError(ValueError):
    """Base class — the /manage route converts all subclasses to uniform 401."""


class TokenInvalid(TokenError):
    """Token is malformed, signed with an unknown key, or has an unknown aid."""


class TokenExpired(TokenError):
    """Signature valid but `exp` is in the past."""


class TokenActionMismatch(TokenError):
    """Signature valid but `act` does not match the expected action."""


class TokenAlreadyUsed(TokenError):
    """Signature valid but this token has already been consumed (replay)."""


# ----------------------------------------------------------------- helpers

def _b64url_encode(raw: bytes) -> str:
    """Base64url encode, strip padding — URL-safe."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    """Base64url decode, tolerating missing `=` padding."""
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sha256_hex(token: str) -> str:
    """Stable hash of the full token for the `used_tokens` PK."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _active_secrets() -> list[tuple[str, str]]:
    """Return [(kid, secret), ...] — current first, then optional old.

    Callers must handle the empty case; however in practice
    APPOINTMENT_TOKEN_SECRET is required at boot (see rotation runbook).
    """
    out: list[tuple[str, str]] = []
    current = os.environ.get(_SECRET_ENV_VAR)
    if current:
        out.append(("current", current))
    old = os.environ.get(_SECRET_OLD_ENV_VAR)
    if old:
        out.append(("old", old))
    return out


def _compute_sig(secret: str, encoded_payload: str) -> str:
    """HMAC-SHA256 of the already-encoded payload, base64url-encoded."""
    digest = hmac.new(
        secret.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


# ----------------------------------------------------------------- sign

def sign(
    appointment_id: int,
    action: TokenAction,
    *,
    expires_in_sec: int = _DEFAULT_TTL_SEC,
    now: datetime | None = None,
) -> str:
    """Produce a URL-safe signed token.

    Uses the **current** secret (kid="current"). Old-kid tokens are
    never minted — they only exist in the wild during the rotation
    validation window and are accepted on verify.
    """
    secrets = _active_secrets()
    if not secrets:
        raise RuntimeError(
            f"{_SECRET_ENV_VAR} must be set to sign manage-appointment tokens"
        )
    kid, secret = secrets[0]
    issued = now if now is not None else datetime.now(timezone.utc)
    iat = int(issued.timestamp())
    payload = {
        "aid": int(appointment_id),
        "act": action.value,
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
    expected_action: TokenAction,
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> int:
    """Validate + consume a token; return its appointment_id.

    Stages (each raises a different ``TokenError`` subclass): shape
    check + signature -> ``TokenInvalid``; ``exp`` -> ``TokenExpired``;
    ``act`` -> ``TokenActionMismatch``; unknown aid -> ``TokenInvalid``;
    atomic INSERT into ``used_tokens`` -> ``TokenAlreadyUsed`` on
    conflict. The HTTP layer catches the base class and returns a
    uniform 401 body.
    """
    payload = _decode_and_verify_signature(token)
    _check_expiry(payload, now)
    _check_action(payload, expected_action)
    appointment_id = int(payload["aid"])
    _check_appointment_exists(appointment_id, db_path)
    _consume_or_raise(
        token=token,
        action=expected_action.value,
        appointment_id=appointment_id,
        db_path=db_path,
        now=now if now is not None else datetime.now(timezone.utc),
    )
    return appointment_id


# ----------------------------------------------------------------- verify stages

def _decode_and_verify_signature(token: str) -> dict:
    """Return the decoded payload dict or raise TokenInvalid.

    Per-kid secret pool: ``kid="old"`` -> OLD only (missing OLD fails
    closed); ``kid="current"`` -> every active secret so a token signed
    seconds before the operator promotes a new secret still verifies
    under what is now OLD; unknown kid -> reject up front.
    """
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
    payload_kid = payload.get("kid", "current")
    if payload_kid not in KNOWN_KIDS:
        raise TokenInvalid("unknown kid")
    active = _active_secrets()
    candidates = (
        [(k, s) for k, s in active if k == "old"]
        if payload_kid == "old" else active
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


def _check_action(payload: dict, expected: TokenAction) -> None:
    act = payload.get("act")
    if act != expected.value:
        raise TokenActionMismatch(
            f"expected action {expected.value!r}, got {act!r}"
        )


def _check_appointment_exists(
    appointment_id: int, db_path: str | Path,
) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT 1 FROM appointments WHERE id = ?", (appointment_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise TokenInvalid("unknown appointment")


def _consume_or_raise(
    *,
    token: str,
    action: str,
    appointment_id: int,
    db_path: str | Path,
    now: datetime,
) -> None:
    """INSERT OR IGNORE into used_tokens; raise if row already existed."""
    token_hash = _sha256_hex(token)
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO used_tokens "
            "(token_hash, used_at, action, appointment_id) "
            "VALUES (?, ?, ?, ?)",
            (token_hash, now.isoformat(), action, appointment_id),
        )
        conn.commit()
        if cursor.rowcount != 1:
            raise TokenAlreadyUsed("token already consumed")
    finally:
        conn.close()
