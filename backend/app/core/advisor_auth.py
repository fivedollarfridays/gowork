"""Advisor authentication — per-token, city-scoped (T12.31).

Implements the Option A design from ``docs/security/advisor-auth.md``:
a server-side ``advisor_tokens`` row (created by m007) keyed on
``SHA256(plaintext)`` with a single ``city`` claim per row. The
FastAPI dependency :func:`require_advisor_token` returns the
``(advisor_id, city)`` tuple that every advisor-scoped route threads
through its repository layer.

Every auth failure — missing row, revoked row, expired row — returns
HTTP **401** with the byte-identical body
``{"detail": "Invalid advisor token"}``. No enumeration oracle.

This module deliberately uses synchronous ``sqlite3`` rather than
SQLAlchemy async: the lookup is a single ``SELECT`` against a tiny
table (<100 rows in production) and the surrounding advisor-inbox
routes are all sync handlers that share the same DB path.
"""

from __future__ import annotations

import hashlib
import hmac
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Header, HTTPException

from app.routes import _appointments_helpers as _db_helpers

__all__ = [
    "hash_advisor_id",
    "hash_token",
    "require_advisor_token",
    "revoke_token",
    "validate_token",
]

_INVALID_DETAIL = "Invalid advisor token"


def hash_token(plaintext: str) -> str:
    """Return the SHA256 hex digest of a plaintext advisor token.

    Plaintext must never be persisted; callers pipe directly into this
    helper before any DB write.
    """
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def hash_advisor_id(advisor_id: str) -> str:
    """SHA256 hex of the advisor id — used in audit payloads."""
    return hashlib.sha256(advisor_id.encode("utf-8")).hexdigest()


def validate_token(
    db_path: str | Path,
    plaintext: str,
    *,
    now: datetime | None = None,
) -> tuple[str, str] | None:
    """Return ``(advisor_id, city)`` or ``None``.

    Uses ``hmac.compare_digest`` against the PK lookup so a timing
    comparison cannot leak whether the row existed. ``None`` is
    returned for every failure mode: missing row, revoked row,
    expired row. Callers convert to a uniform 401 at the route layer.
    """
    h = hash_token(plaintext)
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT token_hash, advisor_id, city, revoked_at, expires_at "
            "FROM advisor_tokens WHERE token_hash = ?",
            (h,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    stored_hash, advisor_id, city, revoked_at, expires_at = row
    if not hmac.compare_digest(stored_hash, h):
        return None  # pragma: no cover — PK lookup guarantees equality
    if revoked_at is not None:
        return None
    if _is_expired(expires_at, now=now):
        return None
    return advisor_id, city


def revoke_token(db_path: str | Path, advisor_id: str) -> int:
    """Revoke every active token for ``advisor_id``. Return row count."""
    ts = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            "UPDATE advisor_tokens SET revoked_at = ? "
            "WHERE advisor_id = ? AND revoked_at IS NULL",
            (ts, advisor_id),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def require_advisor_token(
    x_admin_key: str = Header(...),
) -> tuple[str, str]:
    """FastAPI dependency — return ``(advisor_id, city)`` or 401.

    Resolves the DB path via the shared appointments helper so tests
    can monkeypatch a single ``_resolve_db_path`` target.
    """
    db_path = _db_helpers.resolve_db_path()
    result = validate_token(db_path, x_admin_key)
    if result is None:
        raise HTTPException(status_code=401, detail=_INVALID_DETAIL)
    return result


def _is_expired(expires_at: str | None, *, now: datetime | None) -> bool:
    """Return True iff ``expires_at`` (ISO-8601) is in the past."""
    if not expires_at:
        return False
    cur = now or datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(
            str(expires_at).replace("Z", "+00:00"),
        )
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed <= cur
