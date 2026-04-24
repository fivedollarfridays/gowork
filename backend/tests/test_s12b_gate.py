"""S12b integration gate (T12.35b) — wiring + migrations + flag defaults.

This file is the wiring-and-migrations half of the S12b sprint gate.
Endpoint auth + retention + funnel + load are in
``test_s12b_gate_endpoints.py``. Sections here:

  A. Route registration — every S12b router is mounted in all_routers.
  B. Scheduler lifecycle — enforce_single_worker + three jobs still
     registered; nightly_digest handler is the real orchestrator.
  C. Migration presence + round-trip — all seven migrations apply in
     order; m005/m006/m007 can be rolled back + re-applied cleanly.
  D. m005 + m006 + m007 schema integrity — demo column + tombstones +
     partial advisor_tokens index.
  E. Feature-flag defaults — ENABLE_AI_GENERATION off,
     FEATURE_NIGHTLY_ENABLED + FEATURE_EMAIL_SEND_ENABLED on.
  F. LLM flag audit — flipping ENABLE_AI_GENERATION writes an audit
     row with actor hash + warning logged.
  G. Appointment token rotation — OLD secret honoured until rotation
     window closes.

Helpers live in ``tests._s12b_gate_helpers``.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pytest

from app.core import feature_flags
from app.core.migrations import runner

from tests._s12b_gate_helpers import (
    apply_all_migrations,
    has_column,
    list_tables,
    schema_version,
    seed_appointment_with_session,
)


# ====================================================================
# A. Route registration
# ====================================================================


def test_all_s12b_routers_in_all_routers() -> None:
    """Every S12b router is mounted in app.routes.all_routers."""
    from app.routes import (
        advisor_inbox,
        all_routers,
        appointments_manage,
        compliance,
        documents,
        engagement,
    )

    mounted_ids = {id(r) for r in all_routers}
    expected = [
        ("advisor_inbox", advisor_inbox.router),
        ("appointments_manage", appointments_manage.router),
        ("compliance", compliance.router),
        ("documents", documents.router),
        ("engagement", engagement.router),
    ]
    missing = [name for name, r in expected if id(r) not in mounted_ids]
    assert not missing, (
        f"Missing S12b routers in app.routes.all_routers: {missing}"
    )


def test_s12b_router_prefixes_do_not_collide() -> None:
    """S12b routers sharing a prefix family resolve to distinct routers."""
    from app.routes.advisor_inbox import router as advisor
    from app.routes.appointments import router as appts
    from app.routes.appointments_manage import router as manage
    from app.routes.compliance import router as compliance
    from app.routes.documents import router as documents
    from app.routes.engagement import router as engagement
    from app.routes.engagement_preview import router as preview

    assert advisor.prefix == "/api/advisor"
    assert compliance.prefix == "/api/compliance"
    assert documents.prefix == "/api/documents"
    assert engagement.prefix == "/api/engagement"
    assert preview.prefix == "/api/engagement"
    assert appts.prefix == "/api/appointments"
    assert manage.prefix == "/api/appointments"
    assert appts is not manage
    assert engagement is not preview


# ====================================================================
# B. Scheduler lifecycle
# ====================================================================


@pytest.fixture
def _isolated_scheduler(monkeypatch):
    """Scheduler scoped to a single test — skips sched.start()."""
    from app.core import scheduler as sched_mod

    monkeypatch.setattr(sched_mod, "_TESTING", True)
    sched_mod._reset_for_tests()
    yield sched_mod
    sched_mod._reset_for_tests()


def test_scheduler_rejects_web_concurrency_2(
    monkeypatch: pytest.MonkeyPatch, _isolated_scheduler,
) -> None:
    """enforce_single_worker raises when WEB_CONCURRENCY != "1"."""
    monkeypatch.setenv("WEB_CONCURRENCY", "2")
    with pytest.raises(RuntimeError, match="WEB_CONCURRENCY=1"):
        _isolated_scheduler.enforce_single_worker()


def test_three_scheduler_jobs_still_registered(_isolated_scheduler) -> None:
    """S12a T12.3's three jobs are still wired after S12b."""
    _isolated_scheduler.start_scheduler()
    job_ids = {j.id for j in _isolated_scheduler.get_scheduler().get_jobs()}
    assert {
        "nightly_digest", "stall_scan", "appointment_reminders",
    }.issubset(job_ids), f"scheduler missing jobs: {job_ids}"


def test_nightly_digest_handler_is_real_orchestrator(
    _isolated_scheduler,
) -> None:
    """nightly_digest handler resolves to scripts.nightly_digest — not a stub."""
    _isolated_scheduler.start_scheduler()
    job = _isolated_scheduler.get_scheduler().get_job("nightly_digest")
    assert job is not None
    assert job.func.__module__ == "scripts.nightly_digest"
    assert not job.func.__name__.endswith("_stub")


def test_main_lifespan_wires_scheduler() -> None:
    """app.main.lifespan imports enforce_single_worker + start_scheduler."""
    import inspect

    from app import main as main_mod

    source = inspect.getsource(main_mod.lifespan)
    assert "enforce_single_worker" in source
    assert "start_scheduler" in source


# ====================================================================
# C. Migration presence + round-trip
# ====================================================================


def test_all_seven_migrations_apply_in_order(tmp_path: Path) -> None:
    """m001..m007 apply cleanly and leave schema_migrations at version 7."""
    db_path = str(tmp_path / "seven.db")
    apply_all_migrations(db_path)
    assert schema_version(db_path) >= 7, (
        f"expected schema_migrations max version >= 7, "
        f"got {schema_version(db_path)}"
    )


def test_s12b_migrations_round_trip(tmp_path: Path) -> None:
    """m005/m006/m007 rollback + re-apply round-trip cleanly from m004."""
    db_path = str(tmp_path / "s12b_roundtrip.db")
    apply_all_migrations(db_path)
    assert has_column(db_path, "sessions", "demo")
    assert has_column(db_path, "engagement_events", "deleted_at")
    assert "advisor_tokens" in list_tables(db_path)
    assert "compliance_audit" in list_tables(db_path)

    rolled = runner.rollback(db_path, target_version=4)
    assert any(name.startswith("m005") for name in rolled)
    assert any(name.startswith("m006") for name in rolled)
    assert any(name.startswith("m007") for name in rolled)

    assert not has_column(db_path, "sessions", "demo")
    assert not has_column(db_path, "engagement_events", "deleted_at")
    assert "advisor_tokens" not in list_tables(db_path)
    assert "compliance_audit" not in list_tables(db_path)

    apply_all_migrations(db_path)
    assert has_column(db_path, "sessions", "demo")
    assert has_column(db_path, "engagement_events", "deleted_at")
    assert "advisor_tokens" in list_tables(db_path)
    assert "compliance_audit" in list_tables(db_path)


# ====================================================================
# D. m005 + m006 + m007 schema integrity
# ====================================================================


def test_m005_sessions_demo_column_default_false(tmp_path: Path) -> None:
    """sessions.demo exists with default FALSE after m005."""
    db_path = str(tmp_path / "demo_col.db")
    apply_all_migrations(db_path)
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("PRAGMA table_info(sessions)").fetchall()
    finally:
        conn.close()
    demo_row = next((r for r in rows if r[1] == "demo"), None)
    assert demo_row is not None, "sessions.demo column missing after m005"
    dflt = str(demo_row[4]).upper() if demo_row[4] is not None else ""
    assert dflt in ("FALSE", "0"), (
        f"sessions.demo default should be FALSE/0, got {dflt!r}"
    )


def test_m006_tombstone_columns_on_all_three_tables(tmp_path: Path) -> None:
    """m006 adds deleted_at + deleted_reason on the three sensitive tables."""
    db_path = str(tmp_path / "tomb.db")
    apply_all_migrations(db_path)
    for table in ("record_profiles", "resume_versions", "engagement_events"):
        assert has_column(db_path, table, "deleted_at"), (
            f"{table}.deleted_at missing after m006"
        )
        assert has_column(db_path, table, "deleted_reason"), (
            f"{table}.deleted_reason missing after m006"
        )


def test_m007_advisor_tokens_partial_index_exists(tmp_path: Path) -> None:
    """m007 creates a partial index on revoked_at IS NULL."""
    db_path = str(tmp_path / "advidx.db")
    apply_all_migrations(db_path)
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type='index' AND name='idx_advisor_tokens_active'"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, "idx_advisor_tokens_active missing"
    assert "revoked_at IS NULL" in (row[0] or ""), (
        f"index not partial on revoked_at IS NULL — got: {row[0]!r}"
    )


# ====================================================================
# E. Feature-flag defaults
# ====================================================================


@pytest.fixture
def _clean_flag_env(monkeypatch: pytest.MonkeyPatch):
    """Remove env overrides for the three flags + reset runtime state."""
    for env_name in (
        "FEATURE_ENABLE_AI_GENERATION",
        "FEATURE_FEATURE_NIGHTLY_ENABLED",
        "FEATURE_FEATURE_EMAIL_SEND_ENABLED",
    ):
        monkeypatch.delenv(env_name, raising=False)
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


def test_ai_generation_default_off(_clean_flag_env) -> None:
    """ENABLE_AI_GENERATION defaults to False (production posture)."""
    assert feature_flags.is_enabled("ENABLE_AI_GENERATION") is False


def test_nightly_enabled_default_on(_clean_flag_env) -> None:
    """FEATURE_NIGHTLY_ENABLED defaults to True."""
    assert feature_flags.is_enabled("FEATURE_NIGHTLY_ENABLED") is True


def test_email_send_default_on(_clean_flag_env) -> None:
    """FEATURE_EMAIL_SEND_ENABLED defaults to True."""
    assert feature_flags.is_enabled("FEATURE_EMAIL_SEND_ENABLED") is True


# ====================================================================
# F. LLM flag audit — flipping emits audit row + warning
# ====================================================================


def _route_audit_to_db(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Point feature_flags.get_settings at ``db_path`` for audit writes."""
    class _FakeSettings:
        database_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setattr(
        feature_flags, "get_settings", lambda: _FakeSettings(),
    )


def _read_latest_audit_row(db_path: str) -> tuple | None:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT flag_name, new_value, actor_token_hash, reason "
            "FROM feature_flag_audit "
            "WHERE flag_name = 'ENABLE_AI_GENERATION' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()


def test_flipping_ai_generation_writes_audit_row_and_warns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    _clean_flag_env,
) -> None:
    """Toggling ENABLE_AI_GENERATION=true writes audit + logs PII warning."""
    from app.routes import admin_flags as admin_flags_mod

    db_path = str(tmp_path / "audit.db")
    apply_all_migrations(db_path)
    _route_audit_to_db(db_path, monkeypatch)

    body = admin_flags_mod.FlagToggleRequest(
        enabled=True, reason="gate-test-flip",
    )
    with caplog.at_level(logging.WARNING, logger="app.routes.admin_flags"):
        summary = admin_flags_mod._apply_toggle(
            "ENABLE_AI_GENERATION",
            body,
            actor_token="gate-actor",
            source_ip="127.0.0.1",
        )

    assert summary["enabled"] is True
    assert summary["flag_name"] == "ENABLE_AI_GENERATION"
    assert any(
        "data processing agreement" in rec.message.lower()
        or "pii" in rec.message.lower()
        for rec in caplog.records
    ), (
        f"expected a PII/DPA warning log, got: "
        f"{[r.message for r in caplog.records]}"
    )

    row = _read_latest_audit_row(db_path)
    assert row is not None, "no feature_flag_audit row written"
    flag_name, new_value, actor_hash, reason = row
    assert flag_name == "ENABLE_AI_GENERATION"
    assert new_value == "true"
    assert reason == "gate-test-flip"
    # Actor token must be stored hashed (SHA256 hex is 64 chars).
    assert len(actor_hash) == 64
    assert actor_hash != "gate-actor"


# ====================================================================
# G. Appointment token rotation — OLD secret window
# ====================================================================


def _mint_under_secret(
    monkeypatch: pytest.MonkeyPatch, secret: str, appointment_id: int = 1,
) -> str:
    """Mint a VIEW token with ``secret`` set as CURRENT (no OLD)."""
    from app.modules.appointments import tokens as appt_tokens

    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", secret)
    monkeypatch.delenv("APPOINTMENT_TOKEN_SECRET_OLD", raising=False)
    return appt_tokens.sign(appointment_id, appt_tokens.TokenAction.VIEW)


def test_old_secret_accepted_during_rotation_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Token minted with OLD secret validates while OLD is set; rejects after."""
    from app.modules.appointments import tokens as appt_tokens

    db_path = str(tmp_path / "rot.db")
    apply_all_migrations(db_path)
    seed_appointment_with_session(db_path, appointment_id=1)

    old_secret = "gate-old-secret-aaaaaaaaaaaaaaaaaaaaaaaa"
    new_secret = "gate-new-secret-bbbbbbbbbbbbbbbbbbbbbbbb"

    # Phase 1: mint pre-rotation token.
    token_pre_rotation = _mint_under_secret(monkeypatch, old_secret)

    # Phase 2: rotation window — NEW current, OLD still accepted.
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", new_secret)
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET_OLD", old_secret)
    aid = appt_tokens.verify(
        token_pre_rotation,
        appt_tokens.TokenAction.VIEW,
        db_path=db_path,
    )
    assert aid == 1

    # Phase 3: rotation window closed — OLD removed. New old-era tokens reject.
    second_old_token = _mint_under_secret(monkeypatch, old_secret)
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", new_secret)
    monkeypatch.delenv("APPOINTMENT_TOKEN_SECRET_OLD", raising=False)
    with pytest.raises(appt_tokens.TokenInvalid):
        appt_tokens.verify(
            second_old_token,
            appt_tokens.TokenAction.VIEW,
            db_path=db_path,
        )
