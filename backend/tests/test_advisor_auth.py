"""Migration + token-helper tests for advisor auth (T12.31).

Split out of ``test_advisor_inbox.py`` so neither file crosses the
400-line architecture limit. Covers:

* m007 migration round-trip (``advisor_tokens`` table + partial index).
* ``advisor_auth`` helpers — ``hash_token``, ``validate_token``,
  ``revoke_token`` — with revoked + expired + missing row paths.

Route-level + dependency-level behaviour lives in
``test_advisor_inbox.py``.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from tests._advisor_helpers import (
    _TOKEN,
    insert_advisor_token,
)

_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def migrated_db(tmp_path: Path) -> str:
    """Temp DB with the full migration chain (through m007)."""
    db_path = str(tmp_path / "advisor_auth.db")
    runner.apply_pending(db_path)
    return db_path


# --------------------------------------------------------------- migration


def test_m007_creates_advisor_tokens_table(migrated_db: str) -> None:
    """advisor_tokens table + expected columns + partial index."""
    conn = sqlite3.connect(migrated_db)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='advisor_tokens'"
        ).fetchone()
        assert row is not None
        cols = {
            c[1] for c in conn.execute(
                "PRAGMA table_info(advisor_tokens)"
            ).fetchall()
        }
        assert cols == {
            "token_hash", "advisor_id", "city",
            "issued_at", "revoked_at", "expires_at",
        }
        indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='advisor_tokens'"
            ).fetchall()
        }
        assert "idx_advisor_tokens_advisor_id" in indexes
        assert "idx_advisor_tokens_active" in indexes
    finally:
        conn.close()


def test_m007_downgrade_clean(tmp_path: Path) -> None:
    """Downgrade m007 removes advisor_tokens + its indexes."""
    db_path = str(tmp_path / "m007_down.db")
    runner.apply_pending(db_path)
    from app.core.migrations import m007_advisor_tokens as m007
    conn = sqlite3.connect(db_path)
    try:
        m007.downgrade(conn)
        conn.commit()
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "advisor_tokens" not in tables
    finally:
        conn.close()


# --------------------------------------------------------------- token helpers


def test_hash_token_is_sha256_hex() -> None:
    """hash_token returns a stable 64-char hex digest."""
    from app.core.advisor_auth import hash_token
    h = hash_token("mw_adv_example")
    assert isinstance(h, str)
    assert len(h) == 64
    assert hash_token("mw_adv_example") == h  # deterministic


def test_validate_token_returns_advisor_and_city(migrated_db: str) -> None:
    """Valid row → (advisor_id, city)."""
    from app.core.advisor_auth import validate_token
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    result = validate_token(migrated_db, _TOKEN)
    assert result == ("adv-jane", "montgomery")


def test_validate_token_rejects_revoked_row(migrated_db: str) -> None:
    """Revoked row → None."""
    from app.core.advisor_auth import validate_token
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery", revoked=True,
    )
    assert validate_token(migrated_db, _TOKEN) is None


def test_validate_token_rejects_expired_row(migrated_db: str) -> None:
    """Row with expires_at in the past → None."""
    from app.core.advisor_auth import validate_token
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
        expires_at=_NOW - timedelta(days=1),
    )
    assert validate_token(migrated_db, _TOKEN, now=_NOW) is None


def test_validate_token_missing_row_returns_none(migrated_db: str) -> None:
    """Unknown plaintext → None (no enumeration via exception type)."""
    from app.core.advisor_auth import validate_token
    assert validate_token(migrated_db, "mw_adv_nonexistent") is None


def test_revoke_token_marks_all_active_rows(migrated_db: str) -> None:
    """revoke_token sets revoked_at on every active row for the advisor."""
    from app.core.advisor_auth import revoke_token, validate_token
    insert_advisor_token(
        migrated_db, _TOKEN, "adv-jane", "montgomery",
    )
    assert revoke_token(migrated_db, "adv-jane") == 1
    assert validate_token(migrated_db, _TOKEN) is None
