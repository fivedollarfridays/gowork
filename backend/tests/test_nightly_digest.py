"""Tests for scripts.nightly_digest — the S12a orchestrator (T12.25).

Covers:
- Empty session pool: accounting row with zero counts
- Single session success: run-through with mocked SendGrid send
- Multi-session with one failure: errors counted, batch not aborted
- Kill switch (FEATURE_NIGHTLY_ENABLED=False): no accounting, no send
- City-scope isolation: only the requested city's sessions processed
- Session without email: skipped with a warning, no SendGrid call
- Accounting row shape: every nightly_run_log column populated
- Plan-refresh stub is a no-op (S12b T12.24 TODO)
- Scheduler registration: the APScheduler handler actually invokes our
  orchestrator (wired up in app.core.scheduler)
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from app.core import feature_flags
from app.core.migrations import runner

# Module under test — imported lazily inside tests so the first test run
# surfaces ImportError (expected during the RED phase).

_NOW = datetime(2026, 4, 23, 2, 0, tzinfo=timezone.utc)


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _reset_feature_flags() -> None:
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "nightly.db")
    runner.apply_pending(path)
    return path


def _seed_session(
    db_path: str,
    session_id: str,
    *,
    email: str | None = "worker@example.com",
    city: str | None = "montgomery",
    barriers: list[str] | None = None,
) -> None:
    """Insert one sessions row and (optionally) an outcomes_records tag for city."""
    profile: dict[str, Any] = {"first_name": "Worker"}
    if email is not None:
        profile["email"] = email
    now_iso = _NOW.isoformat()
    expires = (_NOW + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                session_id,
                now_iso,
                json.dumps(barriers or []),
                json.dumps(profile),
                expires,
            ),
        )
        if city is not None:
            # City tag via outcomes_records.payload_json.city — matches the
            # project's canonical per-session city marker (T12.12 approach).
            conn.execute(
                "INSERT INTO outcomes_records "
                "(session_id, event_type, payload_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (
                    session_id,
                    "city_tag",
                    json.dumps({"city": city}),
                    now_iso,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _install_sendgrid_spy(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Monkeypatch reminder_engine.send_digest so the orchestrator never touches SMTP.

    As of T12.19 the orchestrator routes every digest through
    ``reminder_engine.send_digest`` (adds cooldown + opt-out + kill-switch
    gating). The spy fakes its success path and records the call shape
    the existing tests already asserted against (keyed by ``to``, ``subject``,
    ``category``, ``session_id``).
    """
    calls: list[dict] = []

    def _fake_send_digest(
        session_id: str,
        to_email: str,
        subject: str,
        html: str,
        text: str,
        *,
        db_path: Any = None,
        now: Any = None,
    ):
        calls.append({
            "to": to_email,
            "subject": subject,
            "category": "digest",
            "session_id": session_id,
        })
        from app.modules.engagement.reminder_engine import ReminderDispatchResult
        return ReminderDispatchResult(
            success=True,
            skipped_reason=None,
            category="digest",
            message_id="mid-stub",
        )

    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "send_digest", _fake_send_digest)
    return calls


def _install_compose_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip real digest composition — return a deterministic payload."""
    from app.modules.engagement.digest_composer import DigestResult

    def _fake_compose(session_id, for_date, *, db_path, city=None, now=None):
        return DigestResult(
            subject=f"digest-{session_id}",
            html="<p>body</p>",
            text="body",
            section_counts={"yesterday": 0, "today": 0, "week": 0, "stall": 0},
        )

    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "compose_digest", _fake_compose)


def _install_retro_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip real retro — return a minimal result."""
    from datetime import date as _date
    from app.modules.plan.daily_progress import RetroResult

    def _fake_retro(session_id, for_date, *, db_path):
        return RetroResult(
            session_id=session_id,
            for_date=for_date if isinstance(for_date, _date) else _date.today(),
            actions=[],
            completion_ratio=0.0,
            summary="stub",
        )

    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "run_nightly_retro", _fake_retro)


def _read_accounting_rows(db_path: str) -> list[dict]:
    """Read nightly_run_log rows as dicts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, city, sessions_processed, emails_sent, errors, "
            "duration_sec, start_ts, end_ts FROM nightly_run_log"
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


# -------------------- Tests --------------------


@pytest.mark.anyio
async def test_empty_pool_writes_zero_counts_accounting(
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No sessions → accounting row with sessions_processed=0."""
    _install_compose_stub(monkeypatch)
    _install_retro_stub(monkeypatch)
    _install_sendgrid_spy(monkeypatch)

    from scripts.nightly_digest import run_nightly_digest
    results = await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    )

    assert len(results) == 1
    assert results[0].city == "montgomery"
    assert results[0].sessions_processed == 0
    assert results[0].emails_sent == 0
    assert results[0].errors == 0
    rows = _read_accounting_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["sessions_processed"] == 0
    assert rows[0]["emails_sent"] == 0


@pytest.mark.anyio
async def test_single_session_success(
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One session + email → accounting: processed=1 sent=1 errors=0."""
    _seed_session(db_path, "sid-1")
    _install_compose_stub(monkeypatch)
    _install_retro_stub(monkeypatch)
    sent = _install_sendgrid_spy(monkeypatch)

    from scripts.nightly_digest import run_nightly_digest
    results = await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    )

    assert len(sent) == 1
    assert sent[0]["to"] == "worker@example.com"
    assert sent[0]["category"] == "digest"
    assert results[0].sessions_processed == 1
    assert results[0].emails_sent == 1
    assert results[0].errors == 0


@pytest.mark.anyio
async def test_multi_session_one_failure(
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """3 sessions, middle compose raises → processed=3 sent=2 errors=1."""
    _seed_session(db_path, "sid-1")
    _seed_session(db_path, "sid-2")
    _seed_session(db_path, "sid-3")
    _install_retro_stub(monkeypatch)
    sent = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.digest_composer import DigestResult

    def _selective_compose(session_id, for_date, *, db_path, city=None, now=None):
        if session_id == "sid-2":
            raise RuntimeError("compose blew up")
        return DigestResult(
            subject="ok", html="<p>ok</p>", text="ok",
            section_counts={"yesterday": 0, "today": 0, "week": 0, "stall": 0},
        )

    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "compose_digest", _selective_compose)

    from scripts.nightly_digest import run_nightly_digest
    results = await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    )

    assert results[0].sessions_processed == 3
    assert results[0].emails_sent == 2
    assert results[0].errors == 1
    # Only non-failing sessions sent
    assert len(sent) == 2
    assert {c["session_id"] for c in sent} == {"sid-1", "sid-3"}


@pytest.mark.anyio
async def test_feature_flag_kill_switch(
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With FEATURE_NIGHTLY_ENABLED=False → no run, no accounting row."""
    _seed_session(db_path, "sid-1")
    _install_compose_stub(monkeypatch)
    _install_retro_stub(monkeypatch)
    sent = _install_sendgrid_spy(monkeypatch)

    # Kill switch: force is_enabled to return False for our flag only.
    real_is_enabled = feature_flags.is_enabled

    def _patched(flag_name, default=False):
        if flag_name == "FEATURE_NIGHTLY_ENABLED":
            return False
        return real_is_enabled(flag_name, default=default)

    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd.feature_flags, "is_enabled", _patched)

    from scripts.nightly_digest import run_nightly_digest
    results = await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    )

    assert results == []
    assert _read_accounting_rows(db_path) == []
    assert sent == []


@pytest.mark.anyio
async def test_city_scope_isolation(
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sessions in city A not processed when orchestrator is invoked for city B."""
    _seed_session(db_path, "mty-1", city="montgomery")
    _seed_session(db_path, "mty-2", city="montgomery")
    _seed_session(db_path, "ftw-1", city="fort-worth")
    _seed_session(db_path, "ftw-2", city="fort-worth")
    _seed_session(db_path, "ftw-3", city="fort-worth")
    _install_compose_stub(monkeypatch)
    _install_retro_stub(monkeypatch)
    sent = _install_sendgrid_spy(monkeypatch)

    from scripts.nightly_digest import run_nightly_digest
    results = await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    )

    assert len(results) == 1
    assert results[0].city == "montgomery"
    assert results[0].sessions_processed == 2
    assert results[0].emails_sent == 2
    # Only the montgomery sessions were sent to.
    session_ids = {c["session_id"] for c in sent}
    assert session_ids == {"mty-1", "mty-2"}


@pytest.mark.anyio
async def test_session_without_email_logged_skipped(
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Session with no email skipped: counted processed, not counted sent."""
    _seed_session(db_path, "sid-1", email=None)
    _seed_session(db_path, "sid-2", email="has@example.com")
    _install_compose_stub(monkeypatch)
    _install_retro_stub(monkeypatch)
    sent = _install_sendgrid_spy(monkeypatch)

    from scripts.nightly_digest import run_nightly_digest
    with caplog.at_level(logging.WARNING, logger="scripts.nightly_digest"):
        results = await run_nightly_digest(
            cities=["montgomery"], db_path=db_path, now=_NOW,
        )

    assert results[0].sessions_processed == 2
    assert results[0].emails_sent == 1
    # Only the one with an email got a send call
    assert [c["session_id"] for c in sent] == ["sid-2"]
    # Warning emitted for the no-email session
    assert any("sid-1" in r.message and "no email" in r.message.lower()
               for r in caplog.records)


@pytest.mark.anyio
async def test_accounting_fields_populated(
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After a run, every nightly_run_log column is populated."""
    _seed_session(db_path, "sid-1")
    _install_compose_stub(monkeypatch)
    _install_retro_stub(monkeypatch)
    _install_sendgrid_spy(monkeypatch)

    from scripts.nightly_digest import run_nightly_digest
    await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    )
    rows = _read_accounting_rows(db_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["city"] == "montgomery"
    assert row["sessions_processed"] == 1
    assert row["emails_sent"] == 1
    assert row["errors"] == 0
    assert row["duration_sec"] is not None and row["duration_sec"] >= 0.0
    assert row["start_ts"] is not None
    assert row["end_ts"] is not None


@pytest.mark.anyio
async def test_plan_refresh_invokes_refresher(
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T12.24 — plan-refresh slot now calls plan_refresher.refresh_plan."""
    _seed_session(db_path, "sid-1")
    _install_compose_stub(monkeypatch)
    _install_retro_stub(monkeypatch)
    _install_sendgrid_spy(monkeypatch)

    calls: list[str] = []

    def _spy(session_id, *, db_path, now=None, trigger_reason=None):
        calls.append(session_id)
        from app.modules.plan.plan_refresher import RefreshResult
        return RefreshResult(refreshed=False)

    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "refresh_plan", _spy)

    from scripts.nightly_digest import run_nightly_digest
    await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    )
    assert calls == ["sid-1"]


def test_scheduler_registration_still_fires(monkeypatch: pytest.MonkeyPatch) -> None:
    """The nightly_digest APScheduler job invokes run_nightly_digest()."""
    from app.core import scheduler as sched_mod
    monkeypatch.setattr(sched_mod, "_TESTING", True)
    sched_mod._reset_for_tests()

    called = {"count": 0}

    async def _fake(*, cities=None, db_path=None, now=None):
        called["count"] += 1
        return []

    # Patch the orchestrator target the scheduler wires to.
    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "run_nightly_digest", _fake)

    sched_mod.start_scheduler()
    job = sched_mod.get_scheduler().get_job("nightly_digest")
    assert job is not None
    # Trigger the handler synchronously (it's either async or wraps asyncio.run).
    handler = job.func
    if inspect.iscoroutinefunction(handler):
        asyncio.run(handler())
    else:
        handler()
    assert called["count"] == 1
    sched_mod._reset_for_tests()
