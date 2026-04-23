"""S12a integration gate (T12.35) — wiring + integrity assertions.

This file is the final sprint gate. It does NOT add new features. It
asserts that the 25 prior S12a tasks are wired into the runtime code
path, that migrations can round-trip cleanly, that feature-flag
defaults match the intended production configuration, that the three
scheduler jobs are registered, and that the nightly orchestrator can
handle a scaled-down load.

Sections (one per acceptance criterion group):

  A. Route registration (all_routers + no jobs-prefix collision)
  B. Scheduler lifecycle (single-worker + job registration)
  C. Migration rollback round-trip (m001 -> m002 -> m003 -> m002 -> m001)
  D. 13-table inventory after m002
  E. Feature-flag defaults (yaml-driven when env unset)
  F. OutcomeTracker compat (import sanity for three existing files)
  G. Two-caller pathway hook (monkeypatched; both routes fire)
  H. Load test (scaled-down; gated by RUN_LOAD_TESTS env)

Helpers live in ``tests._s12a_e2e_helpers`` — no new seeding logic here.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from pathlib import Path

import pytest

from app.core import feature_flags
from app.core.migrations import m001_initial, m002_s12_worker_companion, runner


# -------------------- Shared constants --------------------


_EXPECTED_S12_TABLES: frozenset[str] = frozenset({
    "appointments",
    "job_applications",
    "resume_versions",
    "daily_progress_snapshots",
    "engagement_events",
    "plan_history",
    "outcomes_records",
    "reminder_cooldowns",
    "nightly_run_log",
    "scheduler_leases",
    "worker_unavailability",
    "feature_flag_audit",
    "sendgrid_events",
})


# -------------------- Helpers --------------------


def _apply_all_migrations(db_path: str) -> None:
    """Apply m001+m002+m003 via the migration runner."""
    runner.apply_pending(db_path)


def _apply_m001_only(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        m001_initial.upgrade(conn)
        conn.commit()
    finally:
        conn.close()


def _list_tables(db_path: str) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    finally:
        conn.close()
    return {r[0] for r in rows}


def _count(db_path: str, sql: str, params: tuple = ()) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(sql, params).fetchone()
    finally:
        conn.close()
    return int(row[0]) if row else 0


# ====================================================================
# A. Route registration
# ====================================================================


def test_all_s12a_routers_in_all_routers() -> None:
    """Every S12a router is present in the all_routers mount list."""
    from app.routes import (
        admin_flags,
        all_routers,
        appointments,
        engagement_preview,
        jobs_applications,
        sendgrid_webhook,
    )

    # APIRouter is unhashable — compare by identity via id().
    mounted_ids = {id(r) for r in all_routers}
    expected = [
        ("admin_flags", admin_flags.router),
        ("appointments", appointments.router),
        ("engagement_preview", engagement_preview.router),
        ("jobs_applications", jobs_applications.router),
        ("sendgrid_webhook", sendgrid_webhook.router),
    ]
    missing = [name for name, router in expected if id(router) not in mounted_ids]
    assert not missing, (
        f"Missing S12a routers in app.routes.all_routers: {missing}"
    )


def test_no_jobs_prefix_collision() -> None:
    """``/api/jobs`` and ``/api/job-applications`` map to distinct routers."""
    from app.routes.jobs import router as jobs_router
    from app.routes.jobs_applications import router as jobs_apps_router

    assert jobs_router.prefix == "/api/jobs"
    assert jobs_apps_router.prefix == "/api/job-applications"
    assert jobs_router is not jobs_apps_router


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


def test_scheduler_accepts_web_concurrency_1(
    monkeypatch: pytest.MonkeyPatch, _isolated_scheduler,
) -> None:
    """enforce_single_worker passes when WEB_CONCURRENCY is "1"."""
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    _isolated_scheduler.enforce_single_worker()  # no exception


def test_scheduler_accepts_web_concurrency_unset(
    monkeypatch: pytest.MonkeyPatch, _isolated_scheduler,
) -> None:
    """enforce_single_worker defaults to OK when WEB_CONCURRENCY is unset."""
    monkeypatch.delenv("WEB_CONCURRENCY", raising=False)
    _isolated_scheduler.enforce_single_worker()  # no exception


def test_scheduler_rejects_web_concurrency_2(
    monkeypatch: pytest.MonkeyPatch, _isolated_scheduler,
) -> None:
    """enforce_single_worker raises RuntimeError when WEB_CONCURRENCY > 1."""
    monkeypatch.setenv("WEB_CONCURRENCY", "2")
    with pytest.raises(RuntimeError, match="WEB_CONCURRENCY=1"):
        _isolated_scheduler.enforce_single_worker()


def test_three_scheduler_jobs_registered(_isolated_scheduler) -> None:
    """start_scheduler registers nightly_digest, stall_scan, appointment_reminders."""
    _isolated_scheduler.start_scheduler()
    sched = _isolated_scheduler.get_scheduler()
    job_ids = {j.id for j in sched.get_jobs()}
    assert {
        "nightly_digest", "stall_scan", "appointment_reminders",
    }.issubset(job_ids), f"scheduler missing S12a jobs: {job_ids}"


def test_nightly_digest_handler_is_real_orchestrator(
    _isolated_scheduler,
) -> None:
    """The registered nightly_digest callable is the real orchestrator, not a stub."""
    _isolated_scheduler.start_scheduler()
    job = _isolated_scheduler.get_scheduler().get_job("nightly_digest")
    assert job is not None
    func = job.func
    # Real orchestrator lives in scripts.nightly_digest, not scheduler._stub.
    assert func.__module__ == "scripts.nightly_digest", (
        f"nightly_digest handler module is {func.__module__}, "
        f"expected scripts.nightly_digest (handler: {func.__name__})"
    )
    assert func.__name__ == "nightly_digest_job"
    assert not func.__name__.endswith("_stub")


# ====================================================================
# C. Migration rollback round-trip
# ====================================================================


def _seed_session(db_path: str, session_id: str) -> None:
    """Insert one session row so FK-dependent seeds succeed."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, "2026-04-23T00:00:00Z", "[]",
             "2026-05-23T00:00:00Z"),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_m002_rows(db_path: str, session_id: str) -> None:
    """Insert one row into appointments + outcomes_records for the round-trip."""
    now = "2026-04-23T00:00:00Z"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO appointments "
            "(session_id, type, title, starts_at, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, "interview", "T", now, "scheduled", now),
        )
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, "city_tag", '{"city": "montgomery"}', now),
        )
        conn.commit()
    finally:
        conn.close()


def test_migration_rollback_roundtrip(tmp_path: Path) -> None:
    """m001 -> m002 -> m003, seed, rollback to m001, re-apply — session preserved."""
    db_path = str(tmp_path / "roundtrip.db")

    # Up: apply all migrations.
    _apply_all_migrations(db_path)
    assert _EXPECTED_S12_TABLES.issubset(_list_tables(db_path))

    # Seed a session + m002 rows.
    _seed_session(db_path, "sess-roundtrip")
    _seed_m002_rows(db_path, "sess-roundtrip")
    assert _count(db_path, "SELECT COUNT(*) FROM sessions") == 1
    assert _count(db_path, "SELECT COUNT(*) FROM appointments") == 1
    assert _count(db_path, "SELECT COUNT(*) FROM outcomes_records") == 1

    # Down: roll back to m001 (target_version=1). m003 is a no-op
    # downgrade; m002 drops the 13 tables.
    rolled = runner.rollback(db_path, target_version=1)
    assert "m002_s12_worker_companion" in rolled

    tables = _list_tables(db_path)
    leftover = _EXPECTED_S12_TABLES & tables
    assert not leftover, f"rollback left S12 tables: {leftover}"
    assert "sessions" in tables, "rollback clobbered m001 sessions table"
    assert _count(db_path, "SELECT COUNT(*) FROM sessions") == 1

    # Up again — S12 tables return empty, session data preserved.
    _apply_all_migrations(db_path)
    assert _EXPECTED_S12_TABLES.issubset(_list_tables(db_path))
    assert _count(db_path, "SELECT COUNT(*) FROM sessions") == 1
    assert _count(db_path, "SELECT COUNT(*) FROM appointments") == 0
    assert _count(db_path, "SELECT COUNT(*) FROM outcomes_records") == 0


# ====================================================================
# D. 13 tables inventory
# ====================================================================


def test_all_13_tables_present_after_m002(tmp_path: Path) -> None:
    """All 13 S12 tables created by m002 are present after upgrade."""
    db_path = str(tmp_path / "inventory.db")
    _apply_m001_only(db_path)

    conn = sqlite3.connect(db_path)
    try:
        m002_s12_worker_companion.upgrade(conn)
        conn.commit()
    finally:
        conn.close()

    tables = _list_tables(db_path)
    missing = _EXPECTED_S12_TABLES - tables
    assert not missing, f"m002 did not create all 13 tables. Missing: {missing}"


# ====================================================================
# E. Feature-flag defaults (yaml-driven when env unset)
# ====================================================================


@pytest.fixture
def _clean_flag_env(monkeypatch: pytest.MonkeyPatch):
    """Remove env overrides for the three S12a flags + reset runtime state."""
    for env_name in (
        "FEATURE_ENABLE_AI_GENERATION",
        "FEATURE_FEATURE_NIGHTLY_ENABLED",
        "FEATURE_FEATURE_EMAIL_SEND_ENABLED",
    ):
        monkeypatch.delenv(env_name, raising=False)
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


def test_feature_flag_default_ai_generation_off(_clean_flag_env) -> None:
    """ENABLE_AI_GENERATION resolves to False from YAML."""
    assert feature_flags.is_enabled("ENABLE_AI_GENERATION") is False


def test_feature_flag_default_nightly_on(_clean_flag_env) -> None:
    """FEATURE_NIGHTLY_ENABLED resolves to True from YAML."""
    # Default False; YAML says true.
    assert feature_flags.is_enabled("FEATURE_NIGHTLY_ENABLED") is True


def test_feature_flag_default_email_send_on(_clean_flag_env) -> None:
    """FEATURE_EMAIL_SEND_ENABLED resolves to True from YAML."""
    assert feature_flags.is_enabled("FEATURE_EMAIL_SEND_ENABLED") is True


# ====================================================================
# F. OutcomeTracker compat
# ====================================================================


def test_outcome_tracker_test_files_import_clean() -> None:
    """The three pre-S12 outcome test files still import without error."""
    import importlib

    for modname in (
        "tests.test_outcome_tracker",
        "tests.test_outcome_aggregator",
        "tests.test_s8_coverage_gaps",
    ):
        module = importlib.import_module(modname)
        assert module is not None


# ====================================================================
# G. Two-caller pathway hook (both /api/pathway and /api/plan/.../intelligence)
# ====================================================================


@pytest.mark.anyio
async def test_two_caller_pathway_hook_fires_from_both_routes(
    client, test_engine, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gate-level mirror of T12.32 contract — both routes hit the linker."""
    from tests._s12a_e2e_helpers import seed_session_async

    sid = "00000000-0000-4000-8000-ba7e00000099"
    await seed_session_async(
        test_engine, sid, ["dmv_license"], auth_token="tok-gate-two",
    )

    captured: list[dict] = []

    def _fake_linker(session_id, pathway_result, *, city, db_path):
        captured.append({
            "session_id": session_id,
            "barriers": list(pathway_result.barriers_active),
            "city": city,
        })
        return []

    monkeypatch.setattr(
        "app.routes._intelligence_helpers.auto_generate_placeholders",
        _fake_linker,
    )

    r1 = await client.post(
        "/api/pathway?token=tok-gate-two",
        json={"session_id": sid, "current_wage": 10.0},
    )
    assert r1.status_code == 200, r1.text
    r2 = await client.get(
        f"/api/plan/{sid}/intelligence?token=tok-gate-two&current_wage=10.0",
    )
    assert r2.status_code == 200, r2.text

    assert len(captured) >= 2, (
        f"expected 2+ linker invocations (one per route), got {len(captured)}"
    )
    assert all(c["session_id"] == sid for c in captured)
    assert all("dmv_license" in c["barriers"] for c in captured)


# ====================================================================
# H. Load test — nightly orchestrator scale (gated)
# ====================================================================


_RUN_LOAD = os.environ.get("RUN_LOAD_TESTS") == "1"


@pytest.mark.skipif(
    not _RUN_LOAD,
    reason="scale load test only runs with RUN_LOAD_TESTS=1",
)
def test_nightly_orchestrator_scale_200_sessions_under_10_min(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """200 sessions across 2 cities complete under 600s wall clock."""
    import time

    from scripts.nightly_digest import run_nightly_digest
    from tests._s12a_e2e_helpers import install_sendgrid_spy, seed_session

    db_path = str(tmp_path / "load.db")
    _apply_all_migrations(db_path)

    # Seed 200 sessions: 100 per city.
    for i in range(100):
        seed_session(
            db_path, f"mty-{i:04d}", f"tok-mty-{i:04d}",
            barriers=["expunction"], city="montgomery",
            email=f"w{i}@montgomery.test",
        )
        seed_session(
            db_path, f"ftw-{i:04d}", f"tok-ftw-{i:04d}",
            barriers=["nondisclosure"], city="fort-worth",
            email=f"w{i}@fortworth.test",
        )

    install_sendgrid_spy(monkeypatch)

    start = time.monotonic()
    asyncio.run(run_nightly_digest(
        cities=["montgomery", "fort-worth"], db_path=db_path,
    ))
    elapsed = time.monotonic() - start

    assert elapsed < 600.0, (
        f"nightly orchestrator took {elapsed:.1f}s for 200 sessions, "
        f"expected < 600s"
    )
