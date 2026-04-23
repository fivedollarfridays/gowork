"""Tests for signed manage-appointment tokens (T12.10b).

Covers:
- m004 migration round-trip (creates used_tokens table).
- sign/verify round-trip with kid payload.
- Rejection of tampered, expired, action-mismatched, and unknown-aid tokens.
- Atomic single-use replay protection under threading concurrency.
- Key rotation via APPOINTMENT_TOKEN_SECRET_OLD.
- Uniform 401 response body across every failure mode on /api/appointments/manage.

All secrets are monkeypatched via env vars; no production config touched.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.migrations import runner

# ------------------------------------------------------------------ fixtures

_SECRET_CURRENT = "current-secret-for-tests-only-0123456789"
_SECRET_OLD = "old-secret-for-tests-only-fedcba9876543210"


@pytest.fixture
def migrated_db(tmp_path: Path) -> str:
    """Temp SQLite DB with every migration (including m004) applied."""
    db_path = str(tmp_path / "tokens.db")
    runner.apply_pending(db_path)
    return db_path


@pytest.fixture
def secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set APPOINTMENT_TOKEN_SECRET only (no OLD)."""
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", _SECRET_CURRENT)
    monkeypatch.delenv("APPOINTMENT_TOKEN_SECRET_OLD", raising=False)


@pytest.fixture
def rotating_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set both secrets to simulate key-rotation validation window."""
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", _SECRET_CURRENT)
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET_OLD", _SECRET_OLD)


def _seed_appointment(db_path: str, session_id: str = "sess-1") -> int:
    """Insert a session + one scheduled appointment, return its id."""
    conn = sqlite3.connect(db_path)
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        expires_iso = (
            datetime.now(timezone.utc) + timedelta(days=30)
        ).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, now_iso, "[]", expires_iso),
        )
        starts = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        ends = (datetime.now(timezone.utc) + timedelta(days=2, hours=1)).isoformat()
        cur = conn.execute(
            "INSERT INTO appointments "
            "(session_id, type, title, starts_at, ends_at, location_name, "
            "status, source, created_at) "
            "VALUES (?, 'dmv', 'Test', ?, ?, 'DMV Office', 'scheduled', "
            "'user', ?)",
            (session_id, starts, ends, now_iso),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


# ------------------------------------------------------------------ m004

def test_m004_creates_used_tokens_table(migrated_db: str) -> None:
    """Round-trip: migrations create used_tokens table with UNIQUE on hash."""
    conn = sqlite3.connect(migrated_db)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='used_tokens'"
        ).fetchone()
        assert row is not None
        cols = conn.execute("PRAGMA table_info(used_tokens)").fetchall()
        names = {c[1] for c in cols}
        assert names == {"token_hash", "used_at", "action", "appointment_id"}
        # token_hash is PRIMARY KEY (unique)
        pk_cols = [c[1] for c in cols if c[5] == 1]
        assert pk_cols == ["token_hash"]
    finally:
        conn.close()


def test_m004_rejects_duplicate_token_hash(migrated_db: str) -> None:
    """Insert twice with same hash -> second fails."""
    conn = sqlite3.connect(migrated_db)
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO used_tokens (token_hash, used_at, action, appointment_id) "
            "VALUES (?, ?, ?, ?)",
            ("abc123", now_iso, "cancel", 1),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO used_tokens "
                "(token_hash, used_at, action, appointment_id) "
                "VALUES (?, ?, ?, ?)",
                ("abc123", now_iso, "cancel", 1),
            )
    finally:
        conn.close()


# ------------------------------------------------------------------ sign/verify

def test_sign_verify_round_trip(migrated_db: str, secret_env: None) -> None:
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    token = tokens.sign(aid, tokens.TokenAction.CANCEL)
    result = tokens.verify(
        token, tokens.TokenAction.CANCEL, db_path=migrated_db,
    )
    assert result == aid


def test_verify_rejects_tampered_token(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    token = tokens.sign(aid, tokens.TokenAction.CANCEL)
    # Flip a character in the signature half (after the dot).
    payload, sig = token.split(".", 1)
    flipped = "A" if sig[0] != "A" else "B"
    tampered = f"{payload}.{flipped}{sig[1:]}"
    with pytest.raises(tokens.TokenInvalid):
        tokens.verify(
            tampered, tokens.TokenAction.CANCEL, db_path=migrated_db,
        )


def test_verify_rejects_expired_token(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    past = datetime.now(timezone.utc) - timedelta(days=2)
    token = tokens.sign(
        aid, tokens.TokenAction.CANCEL,
        expires_in_sec=3600, now=past,
    )
    with pytest.raises(tokens.TokenExpired):
        tokens.verify(
            token, tokens.TokenAction.CANCEL, db_path=migrated_db,
        )


def test_verify_rejects_action_mismatch(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    token = tokens.sign(aid, tokens.TokenAction.CANCEL)
    with pytest.raises(tokens.TokenActionMismatch):
        tokens.verify(
            token, tokens.TokenAction.RESCHEDULE, db_path=migrated_db,
        )


def test_verify_rejects_unknown_appointment_id(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.appointments import tokens

    # Valid signature but the appointment id never existed.
    token = tokens.sign(99999, tokens.TokenAction.VIEW)
    with pytest.raises(tokens.TokenInvalid):
        tokens.verify(
            token, tokens.TokenAction.VIEW, db_path=migrated_db,
        )


def test_kid_missing_defaults_to_current(
    migrated_db: str, secret_env: None,
) -> None:
    """Tokens produced without the kid field are treated as kid='current'.

    Backward compat: a token minted by an earlier build that omitted `kid`
    must still verify under the current secret.
    """
    import base64
    import hashlib
    import hmac
    import json

    aid = _seed_appointment(migrated_db)
    payload = {
        "aid": aid,
        "act": "view",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=").decode()
    sig = hmac.new(
        _SECRET_CURRENT.encode(), encoded.encode(), hashlib.sha256,
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    legacy_token = f"{encoded}.{sig_b64}"

    from app.modules.appointments import tokens
    result = tokens.verify(
        legacy_token, tokens.TokenAction.VIEW, db_path=migrated_db,
    )
    assert result == aid


# ------------------------------------------------------------------ rotation

def test_key_rotation_old_kid_still_valid_when_old_secret_set(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Old-kid token signs under old secret; current env has both secrets."""
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    # Phase 1: only OLD secret exists -> signs as kid=current.
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", _SECRET_OLD)
    monkeypatch.delenv("APPOINTMENT_TOKEN_SECRET_OLD", raising=False)
    token = tokens.sign(aid, tokens.TokenAction.VIEW)
    # Phase 2: rotation - new secret promoted, old kept as OLD.
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", _SECRET_CURRENT)
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET_OLD", _SECRET_OLD)
    result = tokens.verify(
        token, tokens.TokenAction.VIEW, db_path=migrated_db,
    )
    assert result == aid


def test_key_rotation_missing_old_invalidates(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Token signed with old kid, but APPOINTMENT_TOKEN_SECRET_OLD unset."""
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    # Sign with OLD as current.
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", _SECRET_OLD)
    monkeypatch.delenv("APPOINTMENT_TOKEN_SECRET_OLD", raising=False)
    token = tokens.sign(aid, tokens.TokenAction.VIEW)
    # Rotate but drop OLD immediately.
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", _SECRET_CURRENT)
    monkeypatch.delenv("APPOINTMENT_TOKEN_SECRET_OLD", raising=False)
    with pytest.raises(tokens.TokenInvalid):
        tokens.verify(
            token, tokens.TokenAction.VIEW, db_path=migrated_db,
        )


# ------------------------------------------------------------------ atomic replay

def test_second_use_after_first_raises_token_already_used(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    token = tokens.sign(aid, tokens.TokenAction.CANCEL)
    tokens.verify(token, tokens.TokenAction.CANCEL, db_path=migrated_db)
    with pytest.raises(tokens.TokenAlreadyUsed):
        tokens.verify(
            token, tokens.TokenAction.CANCEL, db_path=migrated_db,
        )


def test_atomic_single_use_under_concurrency(
    migrated_db: str, secret_env: None,
) -> None:
    """Two threads race to verify the same token; exactly one wins."""
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    token = tokens.sign(aid, tokens.TokenAction.CANCEL)

    barrier = threading.Barrier(2)
    results: dict[str, int] = {"ok": 0, "already_used": 0, "other": 0}
    lock = threading.Lock()

    def worker() -> None:
        barrier.wait()
        try:
            tokens.verify(
                token, tokens.TokenAction.CANCEL, db_path=migrated_db,
            )
            with lock:
                results["ok"] += 1
        except tokens.TokenAlreadyUsed:
            with lock:
                results["already_used"] += 1
        except Exception:  # noqa: BLE001 — catch-all is intentional
            with lock:
                results["other"] += 1

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert results["ok"] == 1, results
    assert results["already_used"] == 1, results
    assert results["other"] == 0, results


# ------------------------------------------------------------------ route layer

@pytest.fixture
def manage_client(
    migrated_db: str, secret_env: None, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """TestClient for the /api/appointments/manage router."""
    from app.routes import appointments_manage

    monkeypatch.setattr(
        appointments_manage, "_resolve_db_path", lambda: migrated_db,
    )
    app = FastAPI()
    app.include_router(appointments_manage.router)
    return TestClient(app)


_UNIFORM_BODY = {"detail": "Invalid or expired manage-appointment token."}


def test_manage_returns_uniform_401_for_all_failures(
    migrated_db: str, manage_client: TestClient,
) -> None:
    """Every failure path returns byte-identical 401 body."""
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)

    # 1. Garbage token (malformed).
    r1 = manage_client.get("/api/appointments/manage?token=junk&action=cancel")

    # 2. Expired token.
    past = datetime.now(timezone.utc) - timedelta(days=10)
    expired = tokens.sign(
        aid, tokens.TokenAction.CANCEL,
        expires_in_sec=3600, now=past,
    )
    r2 = manage_client.get(
        f"/api/appointments/manage?token={expired}&action=cancel",
    )

    # 3. Action mismatch.
    t_cancel = tokens.sign(aid, tokens.TokenAction.CANCEL)
    r3 = manage_client.get(
        f"/api/appointments/manage?token={t_cancel}&action=reschedule",
    )

    # 4. Tampered signature.
    payload, sig = t_cancel.split(".", 1)
    bad = f"{payload}.{'A' if sig[0] != 'A' else 'B'}{sig[1:]}"
    r4 = manage_client.get(
        f"/api/appointments/manage?token={bad}&action=cancel",
    )

    # 5. Replay (use it once, then again).
    t_fresh = tokens.sign(aid, tokens.TokenAction.VIEW)
    ok = manage_client.get(
        f"/api/appointments/manage?token={t_fresh}&action=view",
    )
    assert ok.status_code == 200
    r5 = manage_client.get(
        f"/api/appointments/manage?token={t_fresh}&action=view",
    )

    for resp in (r1, r2, r3, r4, r5):
        assert resp.status_code == 401, resp.text
        assert resp.json() == _UNIFORM_BODY, resp.text


def test_cancel_flow_happy_path(
    migrated_db: str, manage_client: TestClient,
) -> None:
    from app.modules.appointments import scheduler, tokens

    aid = _seed_appointment(migrated_db)
    token = tokens.sign(aid, tokens.TokenAction.CANCEL)
    resp = manage_client.get(
        f"/api/appointments/manage?token={token}&action=cancel",
    )
    assert resp.status_code == 200, resp.text
    updated = scheduler.get(aid, db_path=migrated_db)
    assert updated is not None
    assert updated.status.value == "cancelled"


def test_view_flow_happy_path(
    migrated_db: str, manage_client: TestClient,
) -> None:
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    token = tokens.sign(aid, tokens.TokenAction.VIEW)
    resp = manage_client.get(
        f"/api/appointments/manage?token={token}&action=view",
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "appointment" in body
    assert body["appointment"]["id"] == aid


def test_reschedule_flow_returns_redirect(
    migrated_db: str, manage_client: TestClient,
) -> None:
    from app.modules.appointments import tokens

    aid = _seed_appointment(migrated_db)
    token = tokens.sign(aid, tokens.TokenAction.RESCHEDULE)
    resp = manage_client.get(
        f"/api/appointments/manage?token={token}&action=reschedule",
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["appointment_id"] == aid
    assert "redirect" in body
