"""Magic-link credential CRUD — issuance (T22.7) + validation (T22.8).

Split out of :mod:`app.core.queries_accounts` so the identity-layer
query module stays inside the per-file function-count budget. The
helpers here ONLY touch the ``account_credentials`` table; account
lookup / session claim still lives in ``queries_accounts``.

Both sides of the credential lifecycle hash via
:func:`hash_token` so the on-disk hash is byte-comparable across the
mint and validate paths — drift here would silently break every
magic-link sign-in.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


_INSERT_CREDENTIAL_SQL = (
    "INSERT INTO account_credentials "
    "(account_id, credential_type, credential_value_hash, expires_at) "
    "VALUES (:aid, :ct, :hash, :exp) "
    "RETURNING id"
)


def hash_token(raw_token: str) -> str:
    """SHA-256 hex digest of *raw_token* — the form persisted on disk.

    Single source of truth for credential hashing. Both the issuance
    helper (:func:`mint_magic_link_credential`) and the validation
    helper (:func:`find_unused_credential_by_hash`) MUST route through
    this so the on-disk hash is comparable across both paths.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def _insert_credential_row(
    session: AsyncSession,
    *,
    account_id: int,
    credential_hash: str,
    expires_iso: str,
) -> int:
    """Insert one ``magic_link`` credential row and return its ``id``."""
    result = await session.execute(
        text(_INSERT_CREDENTIAL_SQL),
        {
            "aid": account_id,
            "ct": "magic_link",
            "hash": credential_hash,
            "exp": expires_iso,
        },
    )
    row = result.first()
    await session.commit()
    assert row is not None  # RETURNING always yields the inserted row
    return int(row[0])


async def mint_magic_link_credential(
    session: AsyncSession,
    *,
    account_id: int,
    expires_at: datetime,
) -> tuple[str, int]:
    """Mint a single-use magic-link token for *account_id*.

    Generates ~256 bits of entropy via :func:`secrets.token_urlsafe`,
    persists only the SHA-256 hash, and returns the raw token plus the
    new row's PK. The raw token MUST never land on disk — the route
    layer hands it to the email integration and then drops it.
    """
    raw_token = secrets.token_urlsafe(32)
    credential_hash = hash_token(raw_token)
    expires_iso = expires_at.astimezone(timezone.utc).isoformat()
    credential_id = await _insert_credential_row(
        session,
        account_id=account_id,
        credential_hash=credential_hash,
        expires_iso=expires_iso,
    )
    return raw_token, credential_id


async def find_unused_credential_by_hash(
    session: AsyncSession,
    *,
    token_hash: str,
    credential_type: str = "magic_link",
) -> tuple[int, int] | None:
    """Return ``(account_id, credential_id)`` for a fresh credential or None.

    Single helper handling all three failure modes that must be
    indistinguishable to the caller:

    * row does not exist (token never minted, or hash mismatch)
    * row exists but ``expires_at <= utcnow()``
    * row exists but ``used_at IS NOT NULL`` (already consumed)

    Returning ``None`` for any of those lets the route layer respond
    with a uniform 401 and prevents an oracle attack on the token
    lifecycle.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    result = await session.execute(
        text(
            "SELECT id, account_id FROM account_credentials "
            "WHERE credential_type = :ct "
            "AND credential_value_hash = :h "
            "AND used_at IS NULL "
            "AND expires_at > :now"
        ),
        {"ct": credential_type, "h": token_hash, "now": now_iso},
    )
    row = result.first()
    if row is None:
        return None
    return int(row._mapping["account_id"]), int(row._mapping["id"])


async def mark_credential_used(
    session: AsyncSession, credential_id: int
) -> None:
    """Stamp ``used_at = utcnow()`` on the credential row.

    Idempotent: re-stamping the same row updates ``used_at`` to the
    later timestamp but does not change semantics — the credential is
    already considered consumed by
    :func:`find_unused_credential_by_hash`.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    await session.execute(
        text(
            "UPDATE account_credentials SET used_at = :now WHERE id = :cid"
        ),
        {"now": now_iso, "cid": credential_id},
    )
    await session.commit()
