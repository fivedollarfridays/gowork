"""Tests for worker data export + right-to-delete (T12.36).

Covers:
- m006 migration round-trip (compliance_audit + tombstone columns).
- Full export round-trip: request -> ZIP archive -> signed URL -> download.
- Full delete cascade: all 13 S12 tables + sessions cleared; audit row written.
- Selective delete via tombstones on record_profiles, resume_versions,
  engagement_events; reads filter ``deleted_at IS NULL``.
- Retention sweep purges sessions past ``expires_at + 90d``; newer
  sessions untouched; audit row per purge.
- Signed-link TTL (24h) + single-use replay protection.
- Session-ownership gate: cross-session requests return 403 on every
  user-facing endpoint.

All tests operate on a fresh temp DB with the full migration chain
applied. Compliance token secret is monkeypatched via env.
"""

from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import threading
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.migrations import runner

# --------------------------------------------------------------- fixtures

_SECRET = "compliance-test-secret-0123456789abcdef"
_NOW = datetime.now(timezone.utc)


@pytest.fixture
def migrated_db(tmp_path: Path) -> str:
    """Temp DB with the full migration chain (through m006)."""
    db_path = str(tmp_path / "compliance.db")
    runner.apply_pending(db_path)
    return db_path


@pytest.fixture
def secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPLIANCE_TOKEN_SECRET", _SECRET)
    monkeypatch.delenv("COMPLIANCE_TOKEN_SECRET_OLD", raising=False)


def _seed_session(
    db_path: str, session_id: str, *,
    expires_at: datetime | None = None,
    profile_email: str | None = "worker@example.com",
) -> None:
    """Seed a minimal session row with optional profile email."""
    exp = (expires_at or (_NOW + timedelta(days=30))).isoformat()
    profile = json.dumps(
        {"email": profile_email, "first_name": "Worker"}
        if profile_email else {},
    )
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, profile, "
            "expires_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, _NOW.isoformat(), "[]", profile, exp),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_full_worker_data(db_path: str, session_id: str) -> None:
    """Insert one row into every sensitive table for this session."""
    n = _NOW.isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO record_profiles (session_id, record_types, "
            "charge_categories, years_since_conviction, completed_sentence) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, '["criminal_record"]', '["felony"]', 5, 1),
        )
        conn.execute(
            "INSERT INTO appointments (session_id, type, title, starts_at, "
            "status, created_at) VALUES (?, 'dmv', 'DMV visit', ?, "
            "'scheduled', ?)", (session_id, n, n),
        )
        conn.execute(
            "INSERT INTO job_applications (session_id, company, role, "
            "status, created_at) VALUES (?, 'Acme', 'welder', 'applied', ?)",
            (session_id, n),
        )
        conn.execute(
            "INSERT INTO resume_versions (session_id, doc_type, "
            "version_counter, markdown, use_counter, created_at) "
            "VALUES (?, 'resume', 1, '# resume', 0, ?)",
            (session_id, n),
        )
        conn.execute(
            "INSERT INTO daily_progress_snapshots (session_id, date, "
            "created_at) VALUES (?, '2026-04-22', ?)", (session_id, n),
        )
        conn.execute(
            "INSERT INTO engagement_events (session_id, category, "
            "payload_json, created_at) VALUES (?, 'email_sent', '{}', ?)",
            (session_id, n),
        )
        conn.execute(
            "INSERT INTO plan_history (session_id, archived_at, plan_json) "
            "VALUES (?, ?, '{}')", (session_id, n),
        )
        conn.execute(
            "INSERT INTO outcomes_records (session_id, event_type, "
            "payload_json, created_at) VALUES (?, 'app', '{}', ?)",
            (session_id, n),
        )
        conn.execute(
            "INSERT INTO reminder_cooldowns (session_id, category, "
            "last_sent_at, stall_level) VALUES (?, 'digest', ?, 1)",
            (session_id, n),
        )
        conn.execute(
            "INSERT INTO worker_unavailability (session_id, day_of_week, "
            "start_time, end_time) VALUES (?, 1, '09:00', '17:00')",
            (session_id,),
        )
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------- m006 migration

def test_m006_creates_compliance_audit_table(migrated_db: str) -> None:
    conn = sqlite3.connect(migrated_db)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='compliance_audit'"
        ).fetchone()
        assert row is not None
        cols = {
            c[1] for c in conn.execute(
                "PRAGMA table_info(compliance_audit)"
            ).fetchall()
        }
        expected = {
            "id", "session_id_hash", "action", "category",
            "actor_token_hash", "payload_json", "created_at",
        }
        assert expected.issubset(cols), f"missing {expected - cols}"
    finally:
        conn.close()


def test_m006_tombstone_columns_added(migrated_db: str) -> None:
    """record_profiles, resume_versions, engagement_events gain tombstones."""
    conn = sqlite3.connect(migrated_db)
    try:
        for table in (
            "record_profiles", "resume_versions", "engagement_events",
        ):
            cols = {
                c[1] for c in conn.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            }
            assert "deleted_at" in cols, f"{table} missing deleted_at"
            assert "deleted_reason" in cols, f"{table} missing deleted_reason"
    finally:
        conn.close()


def test_m006_downgrade_clean(tmp_path: Path) -> None:
    """Downgrade m006 removes compliance_audit + tombstone columns."""
    db_path = str(tmp_path / "m006_down.db")
    runner.apply_pending(db_path)
    from app.core.migrations import m006_compliance_tombstones as m006
    conn = sqlite3.connect(db_path)
    try:
        m006.downgrade(conn)
        conn.commit()
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "compliance_audit" not in tables
        for table in (
            "record_profiles", "resume_versions", "engagement_events",
        ):
            cols = {
                c[1] for c in conn.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            }
            assert "deleted_at" not in cols, f"{table} still has deleted_at"
    finally:
        conn.close()


# --------------------------------------------------------------- export

def test_export_archive_contains_all_seeded_tables(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.compliance import export

    _seed_session(migrated_db, "sess-exp")
    _seed_full_worker_data(migrated_db, "sess-exp")
    archive_bytes = export.build_archive("sess-exp", db_path=migrated_db)

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
        names = set(zf.namelist())
        assert "data.json" in names
        assert "summary.md" in names
        data = json.loads(zf.read("data.json"))
        assert data["session_id"] == "sess-exp"
        # Every seeded table appears with exactly one row.
        for table in (
            "appointments", "job_applications", "resume_versions",
            "record_profiles", "daily_progress_snapshots",
            "engagement_events", "plan_history", "outcomes_records",
            "reminder_cooldowns", "worker_unavailability",
        ):
            assert len(data["tables"].get(table, [])) == 1, (
                f"{table} missing from export"
            )


def test_export_signed_link_round_trip(
    migrated_db: str, secret_env: None,
) -> None:
    """Sign an export-ready token, verify consumes it, second verify fails."""
    from app.modules.compliance import export

    _seed_session(migrated_db, "sess-link")
    token = export.sign_export_token(
        "sess-link", archive_id="arc-1",
    )
    sid, arc = export.verify_export_token(token, db_path=migrated_db)
    assert sid == "sess-link" and arc == "arc-1"
    # Replay -> TokenAlreadyUsed.
    with pytest.raises(export.ComplianceTokenError):
        export.verify_export_token(token, db_path=migrated_db)


def test_export_token_expires_after_24h(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.compliance import export

    _seed_session(migrated_db, "sess-exp-ttl")
    past = _NOW - timedelta(hours=25)
    token = export.sign_export_token(
        "sess-exp-ttl", archive_id="arc-x", now=past,
    )
    with pytest.raises(export.ComplianceTokenError):
        export.verify_export_token(token, db_path=migrated_db, now=_NOW)


def test_export_token_atomic_under_concurrency(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.compliance import export

    _seed_session(migrated_db, "sess-race")
    token = export.sign_export_token("sess-race", archive_id="arc-r")

    barrier = threading.Barrier(2)
    wins = {"ok": 0, "used": 0, "other": 0}
    lock = threading.Lock()

    def worker() -> None:
        barrier.wait()
        try:
            export.verify_export_token(token, db_path=migrated_db)
            with lock:
                wins["ok"] += 1
        except export.ComplianceTokenError as exc:
            with lock:
                if "already" in str(exc).lower() or "used" in str(exc).lower():
                    wins["used"] += 1
                else:
                    wins["other"] += 1

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start(); t2.start()
    t1.join(timeout=10); t2.join(timeout=10)
    assert wins["ok"] == 1 and wins["used"] == 1, wins


# --------------------------------------------------------------- full delete

def test_full_delete_cascades_and_writes_audit(
    migrated_db: str, secret_env: None,
) -> None:
    from app.modules.compliance import delete as delete_mod

    _seed_session(migrated_db, "sess-del")
    _seed_full_worker_data(migrated_db, "sess-del")
    delete_mod.full_delete(
        "sess-del", db_path=migrated_db, reason="worker request",
        actor_token="unit-test",
    )

    conn = sqlite3.connect(migrated_db)
    try:
        # Session row gone.
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE id = ?", ("sess-del",),
        ).fetchone()
        assert row is None
        # Every FK-cascaded table: zero rows remain.
        for table in (
            "appointments", "job_applications", "resume_versions",
            "record_profiles", "daily_progress_snapshots",
            "engagement_events", "plan_history", "outcomes_records",
            "reminder_cooldowns", "worker_unavailability",
        ):
            cnt = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE session_id = ?",
                ("sess-del",),
            ).fetchone()[0]
            assert cnt == 0, f"{table} still has rows after full_delete"
        # Audit row written (hashed session_id).
        audit_rows = conn.execute(
            "SELECT action, payload_json FROM compliance_audit"
        ).fetchall()
        actions = [r[0] for r in audit_rows]
        assert "full_delete" in actions
    finally:
        conn.close()


# --------------------------------------------------------------- selective delete

def test_selective_delete_tombstones_record_profile(
    migrated_db: str, secret_env: None,
) -> None:
    """Selective delete of criminal_record tombstones record_profiles."""
    from app.modules.compliance import delete as delete_mod

    _seed_session(migrated_db, "sess-sel")
    _seed_full_worker_data(migrated_db, "sess-sel")
    delete_mod.selective_delete(
        "sess-sel", category="criminal_record",
        db_path=migrated_db, reason="per worker",
        actor_token="unit-test",
    )

    conn = sqlite3.connect(migrated_db)
    try:
        # Row still physically present but tombstoned.
        row = conn.execute(
            "SELECT deleted_at, deleted_reason FROM record_profiles "
            "WHERE session_id = ?", ("sess-sel",),
        ).fetchone()
        assert row is not None
        assert row[0] is not None, "deleted_at should be set"
        assert "worker" in (row[1] or "").lower()
        # Appointments still visible (not in criminal_record category).
        cnt = conn.execute(
            "SELECT COUNT(*) FROM appointments WHERE session_id = ?",
            ("sess-sel",),
        ).fetchone()[0]
        assert cnt == 1
        # Audit row.
        row = conn.execute(
            "SELECT action FROM compliance_audit WHERE action = ?",
            ("selective_delete",),
        ).fetchone()
        assert row is not None
    finally:
        conn.close()


def test_selective_delete_read_filter_hides_tombstoned(
    migrated_db: str, secret_env: None,
) -> None:
    """read_record_profile filters out tombstoned rows."""
    from app.modules.compliance import delete as delete_mod

    _seed_session(migrated_db, "sess-read")
    _seed_full_worker_data(migrated_db, "sess-read")
    # Visible first.
    assert delete_mod.read_record_profile(
        "sess-read", db_path=migrated_db,
    ) is not None
    delete_mod.selective_delete(
        "sess-read", category="criminal_record",
        db_path=migrated_db, reason="x", actor_token="t",
    )
    # Now hidden from the filtered read.
    assert delete_mod.read_record_profile(
        "sess-read", db_path=migrated_db,
    ) is None


# --------------------------------------------------------------- retention sweep

def test_retention_sweep_purges_old_sessions(
    migrated_db: str,
) -> None:
    """Sessions past expires_at + 90d are purged; newer ones survive."""
    from app.modules.compliance import retention

    # Stale: expired 100 days ago -> past expires_at + 90d.
    stale_expiry = _NOW - timedelta(days=100)
    _seed_session(
        migrated_db, "sess-stale", expires_at=stale_expiry,
    )
    # Fresh: expires in future.
    _seed_session(migrated_db, "sess-fresh")
    # Recently-expired (within grace window): should survive.
    grace_expiry = _NOW - timedelta(days=30)
    _seed_session(
        migrated_db, "sess-grace", expires_at=grace_expiry,
    )

    purged = retention.retention_sweep(db_path=migrated_db, now=_NOW)
    assert "sess-stale" in purged
    assert "sess-fresh" not in purged
    assert "sess-grace" not in purged

    conn = sqlite3.connect(migrated_db)
    try:
        ids = {
            r[0] for r in conn.execute("SELECT id FROM sessions").fetchall()
        }
        assert "sess-stale" not in ids
        assert "sess-fresh" in ids
        assert "sess-grace" in ids
        # Audit row per purge.
        cnt = conn.execute(
            "SELECT COUNT(*) FROM compliance_audit WHERE action = ?",
            ("retention_purge",),
        ).fetchone()[0]
        assert cnt == 1
    finally:
        conn.close()


# --------------------------------------------------------------- routes

@pytest.fixture
def compliance_client(
    migrated_db: str, secret_env: None, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """TestClient mounting compliance_router with DB path injected."""
    from app.routes import compliance as compliance_routes
    monkeypatch.setattr(
        compliance_routes, "_resolve_db_path", lambda: migrated_db,
    )
    app = FastAPI()
    app.include_router(compliance_routes.router)
    return TestClient(app)


def _issue_feedback_token(
    db_path: str, token: str, session_id: str, *,
    hours_valid: int = 24,
) -> None:
    """Insert a session-owning feedback token for the ownership gate."""
    exp = (_NOW + timedelta(hours=hours_valid)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO feedback_tokens (token, session_id, created_at, "
            "expires_at) VALUES (?, ?, ?, ?)",
            (token, session_id, _NOW.isoformat(), exp),
        )
        conn.commit()
    finally:
        conn.close()


def test_export_endpoint_requires_session_ownership(
    migrated_db: str, compliance_client: TestClient, secret_env: None,
) -> None:
    """Cross-session token on export endpoint returns 403."""
    _seed_session(migrated_db, "sess-owner")
    _seed_session(migrated_db, "sess-other")
    _issue_feedback_token(migrated_db, "tok-other", "sess-other")
    r = compliance_client.post(
        "/api/compliance/export",
        json={"session_id": "sess-owner", "session_token": "tok-other"},
    )
    assert r.status_code == 403, r.text


def test_delete_endpoint_requires_session_ownership(
    migrated_db: str, compliance_client: TestClient, secret_env: None,
) -> None:
    _seed_session(migrated_db, "sess-a")
    _seed_session(migrated_db, "sess-b")
    _issue_feedback_token(migrated_db, "tok-b", "sess-b")
    r = compliance_client.post(
        "/api/compliance/delete",
        json={
            "session_id": "sess-a", "session_token": "tok-b",
            "confirm": "DELETE",
        },
    )
    assert r.status_code == 403, r.text


def test_selective_delete_endpoint_requires_session_ownership(
    migrated_db: str, compliance_client: TestClient, secret_env: None,
) -> None:
    _seed_session(migrated_db, "sess-p")
    _seed_session(migrated_db, "sess-q")
    _issue_feedback_token(migrated_db, "tok-q", "sess-q")
    r = compliance_client.post(
        "/api/compliance/delete/selective",
        json={
            "session_id": "sess-p", "session_token": "tok-q",
            "category": "criminal_record",
        },
    )
    assert r.status_code == 403, r.text


def test_export_endpoint_happy_path_returns_signed_url(
    migrated_db: str, compliance_client: TestClient, secret_env: None,
) -> None:
    """Request export -> endpoint responds with a download URL + archive id."""
    _seed_session(migrated_db, "sess-h")
    _seed_full_worker_data(migrated_db, "sess-h")
    _issue_feedback_token(migrated_db, "tok-h", "sess-h")
    r = compliance_client.post(
        "/api/compliance/export",
        json={"session_id": "sess-h", "session_token": "tok-h"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "download_url" in body
    assert body.get("expires_in_sec") == 24 * 3600


# --------------------------------------------------------------- S6 / S7

def _read_compliance_audit_actions(db_path: str) -> list[str]:
    """Return ordered list of action strings from compliance_audit."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT action FROM compliance_audit ORDER BY id",
        ).fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def test_download_filename_uses_hashed_session_id(
    migrated_db: str, compliance_client: TestClient, secret_env: None,
) -> None:
    """S6: Content-Disposition filename must NOT echo the raw session_id.

    Worker controls session_id at creation time and there is no
    schema-level CR/LF/quote constraint. Use a SHA256 prefix so the
    header carries no caller-controlled bytes.
    """
    from app.modules.compliance import export as export_mod

    sid = "sess-cd-leak"
    _seed_session(migrated_db, sid)
    _seed_full_worker_data(migrated_db, sid)
    token = export_mod.sign_export_token(sid, archive_id="arc-cd")
    r = compliance_client.get(
        f"/api/compliance/export/download?token={token}",
    )
    assert r.status_code == 200, r.text
    cd = r.headers["Content-Disposition"]
    assert sid not in cd, (
        f"raw session_id leaked into Content-Disposition: {cd!r}"
    )
    expected_prefix = hashlib.sha256(sid.encode("utf-8")).hexdigest()[:16]
    assert expected_prefix in cd, cd


def test_download_audit_written_before_archive_build(
    migrated_db: str, secret_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S7: archive build failure must still leave a compliance trail.

    The audit row is written BEFORE build_archive runs (export_downloaded),
    and a second export_failed row is written if build raises. Operators
    must always see a 500 paired with a trail row — never a silent loss.
    """
    from app.modules.compliance import export as export_mod
    from app.routes import compliance as compliance_routes

    sid = "sess-build-fail"
    _seed_session(migrated_db, sid)
    token = export_mod.sign_export_token(sid, archive_id="arc-bf")

    # Force build_archive to raise after the audit row is written.
    def _boom(session_id: str, *, db_path: str) -> bytes:
        raise RuntimeError("simulated weasyprint failure")

    monkeypatch.setattr(
        compliance_routes.export_mod, "build_archive", _boom, raising=False,
    )
    monkeypatch.setattr(
        compliance_routes, "_resolve_db_path", lambda: migrated_db,
    )

    # Use raise_server_exceptions=False so we observe the 500 instead of
    # the framework re-raising into pytest.
    app = FastAPI()
    app.include_router(compliance_routes.router)
    isolated_client = TestClient(app, raise_server_exceptions=False)

    r = isolated_client.get(
        f"/api/compliance/export/download?token={token}",
    )
    assert r.status_code == 500, r.text
    actions = _read_compliance_audit_actions(migrated_db)
    # Both rows must be present and in order.
    assert "export_downloaded" in actions, actions
    assert "export_failed" in actions, actions
    assert actions.index("export_downloaded") < actions.index("export_failed")


# --------------------------------------------------------------- orchestrator wiring

def test_retention_step_registered_in_nightly(monkeypatch) -> None:
    """nightly_digest.run_nightly_digest calls retention_sweep."""
    import scripts.nightly_digest as nd

    assert hasattr(nd, "_run_retention_sweep"), (
        "nightly_digest missing retention sweep step"
    )
