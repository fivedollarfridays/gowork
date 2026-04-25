"""End-to-end full-pipeline test for the nightly orchestrator (T13.53).

Seeds the worker-companion demo data via T13.2, freezes the wall clock
via the T13.5 ``_fake_clock`` harness, and asserts that every documented
step in :mod:`scripts.nightly_digest` fires once per session, in the
documented order, on both cities, with the right output shape and the
right partial-failure semantics.

Documented step list (extracted from ``scripts/nightly_digest.py``)
==================================================================

For each (city, session) pair the orchestrator runs:

1. ``run_nightly_retro``                — T12.22 daily-progress retro.
2. ``reconcile_session_appointments``   — T12.25a step 2.5 past-appointment
                                            auto-advance.
3. ``refresh_plan``                     — T12.24 plan refresher.
4. ``compose_digest``                   — T12.20 digest composer; internally
                                            invokes the stall detector and the
                                            T12.25b module-status collector.
5. ``send_digest``                      — T12.19 reminder-engine dispatch.
6. ``send_weekly_review`` (Sunday only) — T12.22a piggybacks on the same
                                            ``send_digest`` path so cooldown
                                            + opt-out gating apply uniformly.

After all cities finish (once per nightly run, NOT per-session):

7. ``retention_sweep`` — T12.36 90-day retention purge.

Per-city accounting is written via ``insert_run_row`` after each city
completes (between cities of a multi-city run).

Deviations from the original task brief
---------------------------------------

* The reminder engine (``send_digest``) fires **every day**, including
  Sunday. Sunday adds a *second* dispatch (the weekly review) on top
  of the daily digest — it does NOT replace it.
* The stall detector is invoked inside ``compose_digest`` (and
  ``reminder_engine`` and ``plan_refresher``), not as a standalone
  orchestrator step.

These tests reflect the **actual** code contract, not the brief.

Partial-failure policy
----------------------

The orchestrator is **fail-soft per session**: a raise inside any step
of one session is caught by ``_run_one`` and converted into a
``SessionOutcome(error=...)``; the other sessions in the same city are
unaffected. ``_reconcile_session`` and ``_refresh_session_plan``
additionally swallow their own exceptions internally so the rest of the
per-session pipeline runs even when those steps blow up. Retention
errors are also swallowed so a purge bug never breaks accounting.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from app.core import feature_flags
from app.core.migrations import runner
from app.demo_seed import seed_worker_companion_sessions
from tests._fake_clock import freeze_time
from tests._orchestrator_spies import install_full_spy_set

# Chicago is UTC-5/UTC-6; pick mid-day UTC so the city-local date
# matches the UTC date for both cities.
TUESDAY_UTC = datetime(2026, 4, 21, 12, 0, tzinfo=timezone.utc)  # weekday=1
SUNDAY_UTC = datetime(2026, 4, 26, 12, 0, tzinfo=timezone.utc)   # weekday=6


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _reset_feature_flags() -> None:
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


@pytest.fixture
def seeded_db(tmp_path: Path) -> str:
    """DB with all migrations + the T13.2 worker-companion demo seed.

    The base seed leaves ``profile.email`` unset for medium / hard /
    breakthrough states (the orchestrator returns early there in
    ``_process_session``). For the orchestrator full-run test we want
    every per-session step to reach ``send_digest``, so we backfill a
    deterministic demo email onto every seeded session.
    """
    db_path = str(tmp_path / "orch.db")
    runner.apply_pending(db_path)
    seed_worker_companion_sessions(db_path=db_path, now=TUESDAY_UTC)
    _backfill_demo_emails(db_path)
    return db_path


def _backfill_demo_emails(db_path: str) -> None:
    """Ensure every demo session has a profile email so ``send_digest`` runs."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, profile FROM sessions WHERE demo = 1"
        ).fetchall()
        for sid, profile_json in rows:
            try:
                profile = json.loads(profile_json) if profile_json else {}
            except (json.JSONDecodeError, TypeError):
                profile = {}
            if profile.get("email"):
                continue
            profile["email"] = f"orch-{sid[:8]}@example.invalid"
            profile["first_name"] = profile.get("first_name") or "Demo"
            conn.execute(
                "UPDATE sessions SET profile = ? WHERE id = ?",
                (json.dumps(profile), sid),
            )
        conn.commit()
    finally:
        conn.close()


# -------------------- DB / log helpers --------------------


def _read_audit_rows(db_path: str) -> list[dict]:
    """Read nightly_run_log audit rows as plain dicts (one per city)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, city, sessions_processed, emails_sent, errors, "
            "duration_sec, start_ts, end_ts FROM nightly_run_log "
            "ORDER BY city"
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def _seeded_session_ids_by_city(db_path: str) -> dict[str, list[str]]:
    """Return ``{city: [session_id, ...]}`` for the seeded demo sessions."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT s.id, json_extract(s.profile, '$.city') AS city "
            "FROM sessions s WHERE s.demo = 1"
        ).fetchall()
    finally:
        conn.close()
    out: dict[str, list[str]] = {"montgomery": [], "fort-worth": []}
    for sid, city in rows:
        if city in out:
            out[city].append(sid)
    return out


def _expected_per_session_steps() -> tuple[str, ...]:
    """The five per-session step names in documented order."""
    return ("retro", "reconcile", "refresh", "compose", "send_digest")


def _group_log_by_session(
    log: list[tuple[str, str]],
) -> dict[str, list[str]]:
    """Group the ordered ``(step, session_id)`` log into per-session step lists."""
    out: dict[str, list[str]] = {}
    for step, sid in log:
        out.setdefault(sid, []).append(step)
    return out


# -------------------- Test 1 — every step fires (Tuesday) --------------------


@pytest.mark.anyio
async def test_orchestrator_invokes_every_step(
    seeded_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tuesday (non-Sunday) run: every documented step fires per session, in order.

    Five per-session steps × 5 demo sessions × 1 city = 25 entries.
    Plus exactly one ``retention_sweep`` for the whole run.
    No ``weekly_review`` entries (it's Tuesday).
    """
    log, stash = install_full_spy_set(monkeypatch)
    with freeze_time(TUESDAY_UTC):
        from scripts.nightly_digest import run_nightly_digest
        await run_nightly_digest(
            cities=["montgomery"], db_path=seeded_db, now=TUESDAY_UTC,
        )

    by_session = _group_log_by_session(log)
    expected = _expected_per_session_steps()
    assert len(by_session) == 5, "5 demo sessions per city"
    for sid, steps in by_session.items():
        assert tuple(steps) == expected, (
            f"session {sid} step order wrong: {steps}"
        )
    assert stash["retention_calls"] == 1
    assert stash["weekly_calls"] == [], "weekly_review must NOT fire on Tuesday"


# -------------------- Test 2 — Sunday branch fires weekly review --------------


@pytest.mark.anyio
async def test_orchestrator_runs_sunday_branch(
    seeded_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sunday: every per-session step still fires AND weekly_review fires per session.

    Documents the Sunday policy: weekly review piggybacks on the daily
    digest path — it does NOT replace it. Both ``send_digest`` and
    ``weekly_review`` fire for each session, with weekly running last.
    """
    log, stash = install_full_spy_set(monkeypatch)
    with freeze_time(SUNDAY_UTC):
        from scripts.nightly_digest import run_nightly_digest
        await run_nightly_digest(
            cities=["montgomery"], db_path=seeded_db, now=SUNDAY_UTC,
        )

    by_session = _group_log_by_session(log)
    expected_sunday = _expected_per_session_steps() + ("weekly_review",)
    assert len(by_session) == 5
    for sid, steps in by_session.items():
        assert tuple(steps) == expected_sunday, (
            f"Sunday session {sid} step order wrong: {steps}"
        )
    assert len(stash["weekly_calls"]) == 5


# -------------------- Test 3 — both cities exercised --------------------


@pytest.mark.anyio
async def test_orchestrator_runs_for_both_cities(
    seeded_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both cities are processed; one accounting row per city; sessions stay city-scoped.

    Each city has 5 demo sessions (T13.2 seed contract). The orchestrator
    must process both cities, write exactly one ``nightly_run_log`` row
    per city, and the per-session ``compose_digest`` calls must carry
    the right ``city`` arg for each session.
    """
    log, stash = install_full_spy_set(monkeypatch)
    with freeze_time(TUESDAY_UTC):
        from scripts.nightly_digest import run_nightly_digest
        await run_nightly_digest(
            cities=["montgomery", "fort-worth"], db_path=seeded_db,
            now=TUESDAY_UTC,
        )

    expected_by_city = _seeded_session_ids_by_city(seeded_db)
    assert len(expected_by_city["montgomery"]) == 5
    assert len(expected_by_city["fort-worth"]) == 5

    sids_in_log = {sid for _, sid in log}
    expected_all = set(
        expected_by_city["montgomery"] + expected_by_city["fort-worth"]
    )
    assert sids_in_log == expected_all

    audit_rows = _read_audit_rows(seeded_db)
    assert {r["city"] for r in audit_rows} == {"montgomery", "fort-worth"}
    for row in audit_rows:
        assert row["sessions_processed"] == 5
        assert row["emails_sent"] == 5
        assert row["errors"] == 0

    # Per-session compose calls carry the right city.
    compose_by_sid = {
        c["session_id"]: c["city"] for c in stash["compose_calls"]
    }
    for sid in expected_by_city["montgomery"]:
        assert compose_by_sid[sid] == "montgomery"
    for sid in expected_by_city["fort-worth"]:
        assert compose_by_sid[sid] == "fort-worth"

    # Retention sweep fires exactly once across both cities (per-run, not per-city).
    assert stash["retention_calls"] == 1


# -------------------- Test 4 — partial failure (fail-soft policy) --------------


@pytest.mark.anyio
async def test_orchestrator_partial_failure_continues_or_halts(
    seeded_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One session's ``compose_digest`` raises → other sessions still run.

    Policy in force: **fail-soft per session**. ``_run_one`` catches the
    raise and counts it as ``error=1``; the other 4 sessions in the same
    city complete normally and ``send_digest`` fires for them. Retention
    sweep still runs after the city loop.
    """
    expected_by_city = _seeded_session_ids_by_city(seeded_db)
    poison_sid = sorted(expected_by_city["montgomery"])[0]

    log, stash = install_full_spy_set(
        monkeypatch, compose_raises_for=poison_sid,
    )
    with freeze_time(TUESDAY_UTC):
        from scripts.nightly_digest import run_nightly_digest
        results = await run_nightly_digest(
            cities=["montgomery"], db_path=seeded_db, now=TUESDAY_UTC,
        )

    assert len(results) == 1
    acct = results[0]
    assert acct.sessions_processed == 5
    assert acct.errors == 1
    assert acct.emails_sent == 4

    # The poisoned session has retro/reconcile/refresh/compose but NO send.
    by_session = _group_log_by_session(log)
    assert tuple(by_session[poison_sid]) == (
        "retro", "reconcile", "refresh", "compose",
    ), "post-compose steps must NOT fire after a compose raise"
    # Other sessions completed normally.
    for sid, steps in by_session.items():
        if sid == poison_sid:
            continue
        assert tuple(steps) == _expected_per_session_steps()

    # Retention sweep still ran despite the partial failure.
    assert stash["retention_calls"] == 1


@pytest.mark.anyio
async def test_orchestrator_swallows_refresh_failures(
    seeded_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``refresh_plan`` raise is swallowed inside the per-session pipeline.

    Documents the second tier of fail-soft: ``_refresh_session_plan``
    catches every exception so the digest is still composed and sent
    even when the refresher itself blows up. The session is NOT counted
    as an error because the raise never escapes.
    """
    expected_by_city = _seeded_session_ids_by_city(seeded_db)
    poison_sid = sorted(expected_by_city["montgomery"])[0]

    log, stash = install_full_spy_set(
        monkeypatch, refresh_raises_for=poison_sid,
    )
    with freeze_time(TUESDAY_UTC):
        from scripts.nightly_digest import run_nightly_digest
        results = await run_nightly_digest(
            cities=["montgomery"], db_path=seeded_db, now=TUESDAY_UTC,
        )

    assert results[0].errors == 0, "refresh_plan raise must be swallowed"
    assert results[0].emails_sent == 5
    by_session = _group_log_by_session(log)
    # The full pipeline still fires for the poisoned session; only the
    # refresh return is short-circuited (the raise itself is caught).
    assert tuple(by_session[poison_sid]) == _expected_per_session_steps()


# -------------------- Test 5 — output shapes --------------------


@pytest.mark.anyio
async def test_orchestrator_step_outputs_have_expected_shape(
    seeded_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each step's return value matches the documented contract.

    Verifies:
    - ``RunAccounting`` carries city + counts + duration + start/end ts.
    - ``nightly_run_log`` row mirrors ``RunAccounting`` (every column set).
    - Recorded ``send_digest`` calls carry to/subject/session_id.
    - Recorded ``compose_digest`` calls carry city + a real ``date``.
    """
    log, stash = install_full_spy_set(monkeypatch)
    with freeze_time(TUESDAY_UTC):
        from scripts.nightly_digest import run_nightly_digest
        results = await run_nightly_digest(
            cities=["montgomery"], db_path=seeded_db, now=TUESDAY_UTC,
        )

    _assert_run_accounting_shape(results)
    _assert_audit_row_shape(seeded_db)
    _assert_send_calls_well_formed(stash)
    _assert_compose_calls_well_formed(stash, seeded_db)


def _assert_run_accounting_shape(results: list[Any]) -> None:
    """``RunAccounting`` carries city + counts + duration + start/end ts."""
    from scripts.nightly_accounting import RunAccounting
    assert len(results) == 1
    acct = results[0]
    assert isinstance(acct, RunAccounting)
    assert acct.city == "montgomery"
    assert isinstance(acct.sessions_processed, int)
    assert isinstance(acct.emails_sent, int)
    assert isinstance(acct.errors, int)
    assert isinstance(acct.duration_sec, float)
    assert isinstance(acct.start_ts, datetime)
    assert isinstance(acct.end_ts, datetime)


def _assert_audit_row_shape(db_path: str) -> None:
    """The persisted ``nightly_run_log`` row has every column populated."""
    rows = _read_audit_rows(db_path)
    assert len(rows) == 1
    row = rows[0]
    for col in (
        "city", "sessions_processed", "emails_sent", "errors",
        "duration_sec", "start_ts", "end_ts",
    ):
        assert row[col] is not None, f"column {col} is unset"


def _assert_send_calls_well_formed(stash: dict[str, Any]) -> None:
    """Each ``send_digest`` recorded call carries to/subject/session_id."""
    assert len(stash["send_calls"]) == 5
    for call in stash["send_calls"]:
        assert "@" in call["to"]
        assert call["subject"].startswith("digest-")
        assert call["session_id"]


def _assert_compose_calls_well_formed(
    stash: dict[str, Any], db_path: str,
) -> None:
    """Compose call shape: city is set, for_date is a date, session_id resolves."""
    assert len(stash["compose_calls"]) == 5
    seeded = _seeded_session_ids_by_city(db_path)
    expected = set(seeded["montgomery"])
    seen = set()
    for call in stash["compose_calls"]:
        assert call["city"] == "montgomery"
        assert isinstance(call["for_date"], date)
        seen.add(call["session_id"])
    assert seen == expected


# -------------------- Test 6 — kill switch short-circuits everything ---------


@pytest.mark.anyio
async def test_orchestrator_kill_switch_skips_full_pipeline(
    seeded_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``FEATURE_NIGHTLY_ENABLED=False`` → no step fires, no audit row written."""
    log, stash = install_full_spy_set(monkeypatch)
    real_is_enabled = feature_flags.is_enabled

    def _patched(flag_name: str, default: bool = False) -> bool:
        if flag_name == "FEATURE_NIGHTLY_ENABLED":
            return False
        return real_is_enabled(flag_name, default=default)

    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd.feature_flags, "is_enabled", _patched)

    with freeze_time(TUESDAY_UTC):
        from scripts.nightly_digest import run_nightly_digest
        results = await run_nightly_digest(
            cities=["montgomery"], db_path=seeded_db, now=TUESDAY_UTC,
        )

    assert results == []
    assert log == []
    assert stash["retention_calls"] == 0
    assert _read_audit_rows(seeded_db) == []
