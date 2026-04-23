"""Tests for engagement unsubscribe tokens (T12.21, S12b).

Mirrors the coverage in :mod:`tests.test_appointment_tokens` for the
session-scoped unsubscribe signer. Covers:

- sign/verify round-trip
- tampered / expired signatures rejected
- atomic single-use via used_tokens (concurrent replay rejected)
- UNSUBSCRIBE_TOKEN_SECRET_OLD rotation path
- uniform failure mode surface (verified at route layer in
  tests/test_engagement_routes.py)

The used_tokens table is shared with T12.10b — the ``action`` column
discriminates between appointment actions and the unsubscribe action
(see m004 docstring). session_id is stored in the ``appointment_id``
column because SQLite columns use type affinity rather than strict
types; we rely on that (and on ``action`` = 'unsubscribe') to keep
the two namespaces collision-free.
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner

_SECRET_CURRENT = "unsub-current-secret-for-tests-0123456789abcdef"
_SECRET_OLD = "unsub-old-secret-for-tests-fedcba9876543210aaaa"


@pytest.fixture
def migrated_db(tmp_path: Path) -> str:
    """Temp SQLite DB with every migration (including m004) applied."""
    db_path = str(tmp_path / "unsub.db")
    runner.apply_pending(db_path)
    return db_path


@pytest.fixture
def secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set UNSUBSCRIBE_TOKEN_SECRET only (no OLD)."""
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", _SECRET_CURRENT)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)


@pytest.fixture
def rotating_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set both secrets to simulate key-rotation validation window."""
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", _SECRET_CURRENT)
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", _SECRET_OLD)


# -------------------------------------------------------- sign/verify

def test_sign_verify_round_trip(migrated_db: str, secret_env: None) -> None:
    from app.modules.engagement import unsubscribe_tokens as ut

    token = ut.sign("sess-xyz")
    assert ut.verify(token, db_path=migrated_db) == "sess-xyz"


def test_verify_rejects_tampered_token(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.engagement import unsubscribe_tokens as ut

    token = ut.sign("sess-xyz")
    payload, sig = token.split(".", 1)
    flipped = "A" if sig[0] != "A" else "B"
    bad = f"{payload}.{flipped}{sig[1:]}"
    with pytest.raises(ut.TokenInvalid):
        ut.verify(bad, db_path=migrated_db)


def test_verify_rejects_expired_token(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.engagement import unsubscribe_tokens as ut

    past = datetime.now(timezone.utc) - timedelta(days=40)
    token = ut.sign("sess-xyz", expires_in_sec=3600, now=past)
    with pytest.raises(ut.TokenExpired):
        ut.verify(token, db_path=migrated_db)


def test_verify_rejects_malformed_token(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.engagement import unsubscribe_tokens as ut

    with pytest.raises(ut.TokenInvalid):
        ut.verify("not-a-token-at-all", db_path=migrated_db)


def test_sign_requires_secret_env(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.engagement import unsubscribe_tokens as ut

    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET", raising=False)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)
    with pytest.raises(RuntimeError):
        ut.sign("sess-xyz")


# -------------------------------------------------------- atomic single-use

def test_replay_raises_token_already_used(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.engagement import unsubscribe_tokens as ut

    token = ut.sign("sess-xyz")
    ut.verify(token, db_path=migrated_db)
    with pytest.raises(ut.TokenAlreadyUsed):
        ut.verify(token, db_path=migrated_db)


def test_atomic_single_use_under_concurrency(
    migrated_db: str, secret_env: None,
) -> None:
    """Two threads race to verify the same token; exactly one wins."""
    from app.modules.engagement import unsubscribe_tokens as ut

    token = ut.sign("sess-xyz")

    barrier = threading.Barrier(2)
    results = {"ok": 0, "already_used": 0, "other": 0}
    lock = threading.Lock()

    def worker() -> None:
        barrier.wait()
        try:
            ut.verify(token, db_path=migrated_db)
            with lock:
                results["ok"] += 1
        except ut.TokenAlreadyUsed:
            with lock:
                results["already_used"] += 1
        except Exception:  # noqa: BLE001 — catch-all intentional
            with lock:
                results["other"] += 1

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert results["ok"] == 1, results
    assert results["already_used"] == 1, results
    assert results["other"] == 0, results


def test_used_tokens_row_uses_unsubscribe_action(
    migrated_db: str, secret_env: None,
) -> None:
    """After verify, the used_tokens row has action='unsubscribe'."""
    from app.modules.engagement import unsubscribe_tokens as ut

    ut.verify(ut.sign("sess-xyz"), db_path=migrated_db)
    conn = sqlite3.connect(migrated_db)
    try:
        rows = conn.execute(
            "SELECT action FROM used_tokens WHERE action = 'unsubscribe'"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 1


# -------------------------------------------------------- rotation

def test_key_rotation_old_kid_still_valid(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Token signed under old secret still verifies during rotation window."""
    from app.modules.engagement import unsubscribe_tokens as ut

    # Phase 1: sign under what will become OLD.
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", _SECRET_OLD)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)
    token = ut.sign("sess-xyz")

    # Phase 2: rotate — new current, old kept as OLD.
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", _SECRET_CURRENT)
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", _SECRET_OLD)
    assert ut.verify(token, db_path=migrated_db) == "sess-xyz"


def test_key_rotation_missing_old_invalidates(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without OLD, a token signed under it fails closed."""
    from app.modules.engagement import unsubscribe_tokens as ut

    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", _SECRET_OLD)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)
    token = ut.sign("sess-xyz")

    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", _SECRET_CURRENT)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)
    with pytest.raises(ut.TokenInvalid):
        ut.verify(token, db_path=migrated_db)
