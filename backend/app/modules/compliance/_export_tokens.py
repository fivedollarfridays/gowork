"""Signed single-use download tokens for compliance exports (T12.36).

Internal spoke of :mod:`compliance.export`. Mirrors the T12.10b
manage-appointment token pattern: HMAC-SHA256, ``kid`` + rotation,
atomic single-use via the ``used_tokens`` table (reused — the table's
schema is category-agnostic).

Keeping this in its own file lets ``export.py`` stay under the
functions-per-file ceiling.
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
    "EXPORT_TTL_SEC",
    "ComplianceTokenError",
    "sign_export_token",
    "verify_export_token",
]


EXPORT_TTL_SEC = 24 * 3600
_SECRET_ENV = "COMPLIANCE_TOKEN_SECRET"
_SECRET_OLD_ENV = "COMPLIANCE_TOKEN_SECRET_OLD"

# Kid values the verifier will route to a secret pool. Unknown kids are
# rejected outright — no fall-through to "try every active secret".
# Mirrors the T13.62 hardening in app.modules.appointments.tokens.
_KNOWN_KIDS = frozenset({"current", "old"})


class ComplianceTokenError(ValueError):
    """Any verify-time failure — caller catches a single class."""


def _active_secrets() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    cur = os.environ.get(_SECRET_ENV)
    if cur:
        out.append(("current", cur))
    old = os.environ.get(_SECRET_OLD_ENV)
    if old:
        out.append(("old", old))
    return out


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(secret: str, encoded_payload: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"), encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64url(digest)


def sign_export_token(
    session_id: str, *, archive_id: str,
    expires_in_sec: int = EXPORT_TTL_SEC,
    now: datetime | None = None,
) -> str:
    """Mint a signed single-use token for ``(session_id, archive_id)``."""
    secrets = _active_secrets()
    if not secrets:
        raise RuntimeError(
            f"{_SECRET_ENV} must be set to sign compliance export tokens"
        )
    kid, secret = secrets[0]
    iat = int(
        (now if now is not None else datetime.now(timezone.utc)).timestamp()
    )
    payload = {
        "sid": session_id, "arc": archive_id,
        "exp": iat + int(expires_in_sec), "iat": iat, "kid": kid,
    }
    encoded = _b64url(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    return f"{encoded}.{_sign(secret, encoded)}"


def verify_export_token(
    token: str, *, db_path: str | Path, now: datetime | None = None,
) -> tuple[str, str]:
    """Verify + single-use-consume. Returns ``(session_id, archive_id)``."""
    payload = _decode_and_verify(token)
    _check_expiry(payload, now)
    sid = str(payload["sid"])
    arc = str(payload["arc"])
    _consume_or_raise(
        token=token, archive_id=arc, db_path=db_path,
        now=now if now is not None else datetime.now(timezone.utc),
    )
    return sid, arc


def _decode_and_verify(token: str) -> dict:
    if not token or not isinstance(token, str) or token.count(".") != 1:
        raise ComplianceTokenError("token must be <encoded>.<signature>")
    encoded, provided_sig = token.split(".", 1)
    try:
        raw = _b64url_decode(encoded)
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ComplianceTokenError("invalid payload encoding") from exc
    if not isinstance(payload, dict):
        raise ComplianceTokenError("payload must be a JSON object")
    kid = payload.get("kid", "current")
    if kid not in _KNOWN_KIDS:
        raise ComplianceTokenError("unknown kid")
    active = _active_secrets()
    candidates = (
        [(k, s) for k, s in active if k == "old"]
        if kid == "old" else active
    )
    for _k, secret in candidates:
        expected = _sign(secret, encoded)
        if hmac.compare_digest(expected, provided_sig):
            return payload
    raise ComplianceTokenError("signature does not match any active secret")


def _check_expiry(payload: dict, now: datetime | None) -> None:
    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise ComplianceTokenError("payload missing integer exp")
    cutoff = int(
        (now if now is not None else datetime.now(timezone.utc)).timestamp()
    )
    if exp < cutoff:
        raise ComplianceTokenError("token expired")


def _consume_or_raise(
    *, token: str, archive_id: str, db_path: str | Path, now: datetime,
) -> None:
    """Atomic single-use INSERT into ``used_tokens`` (T12.10b table reuse)."""
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    action = f"compliance_export:{archive_id}"
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    try:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO used_tokens "
            "(token_hash, used_at, action, appointment_id) "
            "VALUES (?, ?, ?, ?)",
            (token_hash, now.isoformat(), action, 0),
        )
        conn.commit()
        if cursor.rowcount != 1:
            raise ComplianceTokenError("token already consumed")
    finally:
        conn.close()
