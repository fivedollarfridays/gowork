"""Scheduled job fire tests (T13.54).

Verifies that APScheduler triggers actually fire at their scheduled times
under the fake-clock harness from T13.5, including missed-fire recovery
behavior driven by ``misfire_grace_time``.

What this file does NOT do
==========================

* It never starts the production AsyncIOScheduler thread. Each test
  builds a fresh ``BackgroundScheduler`` (kept stopped) and uses
  ``_fake_clock.FrozenClock.advance(scheduler=...)`` to fire jobs
  synchronously. This matches the pattern in ``test_fake_clock.py`` and
  keeps the assertions deterministic.
* It does not call into the real DB / SendGrid / digest stack — the
  ``test_real_app_jobs_fire`` test stubs the lazy-imported targets the
  production handler reaches for.

Why misfire tests fire jobs manually
====================================

The fake-clock helper fires every trigger landing inside the advance
window unconditionally — it has no view of ``misfire_grace_time``. The
documented APScheduler behavior is: when the executor finally picks up
a missed job, if ``now - scheduled_run > misfire_grace_time`` the job
is silently skipped (``coalesce=True`` and ``misfire_grace_time=1`` are
the defaults). Tests 4 and 5 therefore replicate that logic via a small
``_fire_respecting_misfire`` helper rather than the harness's
unconditional ``advance(scheduler=...)`` path.
"""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone

import pytest

from tests import _fake_clock as fc


# --------------------------------------------------------------- helpers


def _build_stopped_scheduler():
    """Return a fresh stopped ``BackgroundScheduler`` for use in a test.

    Stopped is the right state for fake-clock fire-walking: jobs added
    while stopped land in ``_pending_jobs`` and ``get_jobs()`` returns
    them. We never call ``.start()`` so no real thread runs.
    """
    from apscheduler.schedulers.background import BackgroundScheduler

    return BackgroundScheduler(timezone=timezone.utc)


def _fire_respecting_misfire(
    scheduler,
    *,
    now: datetime,
    last_check: datetime,
) -> list[str]:
    """Fire jobs in (last_check, now] only if within ``misfire_grace_time``.

    Returns the list of job ids that actually fired (skipped jobs are
    excluded). This is the behavior APScheduler's executor enforces
    when it picks up a job whose ``next_run_time`` already passed.
    """
    fired: list[str] = []
    for job in scheduler.get_jobs():
        next_fire = job.trigger.get_next_fire_time(None, last_check)
        while next_fire is not None and next_fire <= now:
            grace = job.misfire_grace_time
            late_by = (now - next_fire).total_seconds()
            within_grace = grace is None or late_by <= grace
            if within_grace:
                job.func(*job.args, **job.kwargs)
                fired.append(job.id)
            next_fire = job.trigger.get_next_fire_time(next_fire, next_fire)
    return fired


def _stub_appointment_reminders_targets(
    monkeypatch: pytest.MonkeyPatch,
    captured: dict,
    db_path: str = "/tmp/probe.db",
) -> None:
    """Replace the lazy-imported targets reached by the reminders handler.

    The handler resolves these at fire-time, not at module import; so
    monkeypatching the module attributes is enough — we don't need to
    touch the handler factory itself.
    """
    def _fake_scan(*, db_path: str) -> None:
        captured["thread"] = threading.current_thread()
        captured["db_path"] = db_path

    import app.modules.appointments.transactional_emails as te
    monkeypatch.setattr(te, "scan_and_send_reminders", _fake_scan)
    import app.routes._appointments_helpers as helpers
    monkeypatch.setattr(helpers, "resolve_db_path", lambda: db_path)


def _make_async_handler_sync_wrapper(handler) -> "callable":
    """Wrap an async APScheduler handler so it runs synchronously.

    The fake-clock fires ``job.func()`` and never awaits the returned
    coroutine. This wrapper drives it to completion on a fresh loop.
    """
    def _wrapper() -> None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(handler())
        finally:
            loop.close()

    return _wrapper


# --------------------------------------------------------------- Test 1


def test_date_trigger_fires_at_scheduled_time() -> None:
    """A ``DateTrigger`` for now+60s fires after a 60s advance."""
    from apscheduler.triggers.date import DateTrigger

    fired: list[str] = []

    with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
        sched = _build_stopped_scheduler()
        run_at = datetime(2026, 4, 19, 12, 1, 0, tzinfo=timezone.utc)
        sched.add_job(
            lambda: fired.append("hit"),
            trigger=DateTrigger(run_date=run_at, timezone=timezone.utc),
            id="probe_date",
        )

        # Pre-condition: not fired before advance.
        assert fired == []
        clock.advance(60, scheduler=sched)
        assert fired == ["hit"]


# --------------------------------------------------------------- Test 2


def test_cron_trigger_fires_at_next_match() -> None:
    """A daily ``CronTrigger`` for 23:59 fires exactly once across the boundary."""
    from apscheduler.triggers.cron import CronTrigger

    fired: list[int] = []

    # 2026-04-19 is a Sunday; start at 23:58 so a 2-min advance crosses 23:59.
    with fc.freeze_time("2026-04-19T23:58:00+00:00") as clock:
        sched = _build_stopped_scheduler()
        cron = CronTrigger(
            day_of_week="*",
            hour=23,
            minute=59,
            timezone=timezone.utc,
        )
        sched.add_job(
            lambda: fired.append(1),
            trigger=cron,
            id="probe_cron",
        )

        # Sanity-check: trigger's next fire is exactly 23:59 today.
        next_fire = cron.get_next_fire_time(None, datetime.now(timezone.utc))
        assert next_fire.hour == 23 and next_fire.minute == 59

        assert fired == []
        clock.advance(120, scheduler=sched)
        # One fire crossed in the (23:58, 00:00] window — 23:59 hits once,
        # next 23:59 is tomorrow so does not double-fire.
        assert len(fired) == 1


# --------------------------------------------------------------- Test 3


def test_interval_trigger_fires_repeatedly() -> None:
    """A 10-second interval fires three times across a 35-second advance."""
    from apscheduler.triggers.interval import IntervalTrigger

    fired: list[int] = []

    with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
        sched = _build_stopped_scheduler()
        # start_date pinned 5s in the future so the first fire lands at
        # +5s and subsequent fires at +15, +25, +35. Across a 35s advance
        # the (12:00:00, 12:00:35] window catches +5, +15, +25, +35 = 4
        # fires — but +35 is the inclusive boundary so we land on 4. We
        # want exactly 3, so use start_date=+1s and advance 35s: fires at
        # +1, +11, +21, +31 = 4. Tighten to start=+1s and advance=30s:
        # fires at +1, +11, +21 = 3.
        start_at = datetime(2026, 4, 19, 12, 0, 1, tzinfo=timezone.utc)
        sched.add_job(
            lambda: fired.append(1),
            trigger=IntervalTrigger(
                seconds=10,
                start_date=start_at,
                timezone=timezone.utc,
            ),
            id="probe_interval",
        )

        clock.advance(30, scheduler=sched)
        assert len(fired) == 3


# --------------------------------------------------------------- Test 4


def test_missed_fire_recovery_within_grace() -> None:
    """A job whose fire time was missed by < ``misfire_grace_time`` runs.

    Simulates: scheduler was down (or busy) past the scheduled fire
    time. When it wakes back up the executor checks how late the job
    is; if within grace, it runs the job. We replicate that policy via
    ``_fire_respecting_misfire`` (the fake-clock harness fires
    unconditionally).
    """
    from apscheduler.triggers.date import DateTrigger

    fired: list[str] = []

    with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
        sched = _build_stopped_scheduler()
        run_at = datetime(2026, 4, 19, 12, 1, 0, tzinfo=timezone.utc)
        sched.add_job(
            lambda: fired.append("hit"),
            trigger=DateTrigger(run_date=run_at, timezone=timezone.utc),
            id="probe_grace",
            misfire_grace_time=30,
        )

        last_check = datetime.now(timezone.utc)  # 12:00:00
        # Scheduler "down" until 12:01:30 — 30s past the fire time, exactly
        # at the grace boundary. APScheduler treats <= grace as in-grace.
        clock.advance(90)
        now = datetime.now(timezone.utc)
        ran = _fire_respecting_misfire(sched, now=now, last_check=last_check)

        assert fired == ["hit"]
        assert ran == ["probe_grace"]


# --------------------------------------------------------------- Test 5


def test_missed_fire_skipped_beyond_grace() -> None:
    """A job missed by > ``misfire_grace_time`` is silently skipped."""
    from apscheduler.triggers.date import DateTrigger

    fired: list[str] = []

    with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
        sched = _build_stopped_scheduler()
        run_at = datetime(2026, 4, 19, 12, 1, 0, tzinfo=timezone.utc)
        sched.add_job(
            lambda: fired.append("hit"),
            trigger=DateTrigger(run_date=run_at, timezone=timezone.utc),
            id="probe_skipped",
            misfire_grace_time=30,
        )

        last_check = datetime.now(timezone.utc)  # 12:00:00
        # Scheduler "down" until 12:03:20 — 140s past the fire time, well
        # beyond the 30s grace. Documented behavior: silent skip.
        clock.advance(200)
        now = datetime.now(timezone.utc)
        ran = _fire_respecting_misfire(sched, now=now, last_check=last_check)

        assert fired == [], "job should not have fired (beyond grace)"
        assert ran == []


# --------------------------------------------------------------- Test 6


def test_real_app_jobs_fire(monkeypatch: pytest.MonkeyPatch) -> None:
    """Production wiring: ``appointment_reminders`` fires via the scheduler.

    Boots the production scheduler config (``start_scheduler``) with
    ``_TESTING=True`` so no thread starts, replaces the handler's
    lazy-imported scan target with a stub, then advances the clock past
    the 6h interval boundary and asserts the stub ran.

    The handler returned by ``appointment_reminders_handler()`` is a
    coroutine function; the fake-clock harness calls ``job.func(...)``
    which returns the coroutine without awaiting. We drive that
    coroutine to completion via a fresh event loop (see helpers).
    """
    from app.core import scheduler as sched_mod
    from app.core import scheduler_jobs

    captured: dict = {}
    _stub_appointment_reminders_targets(monkeypatch, captured)
    sync_wrapper = _make_async_handler_sync_wrapper(
        scheduler_jobs.appointment_reminders_handler(),
    )

    monkeypatch.setattr(sched_mod, "_TESTING", True, raising=False)
    sched_mod._reset_for_tests()
    try:
        with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
            sched_mod.start_scheduler()
            sched = sched_mod.get_scheduler()
            job = sched.get_job("appointment_reminders")
            assert job is not None, (
                "production wiring missing appointment_reminders job"
            )
            # Swap the async handler for the sync wrapper so the
            # fake-clock can invoke it without awaiting.
            job.modify(func=sync_wrapper)

            assert "db_path" not in captured
            clock.advance(6 * 3600 + 60, scheduler=sched)

            assert captured.get("db_path") == "/tmp/probe.db", (
                "production scheduler did not fire appointment_reminders"
            )
    finally:
        sched_mod._reset_for_tests()


# --------------------------------------------------------------- Test 7


def test_production_jobs_have_sane_misfire_grace_time() -> None:
    """All three S12a/S13 jobs override the 1-second APScheduler default.

    The APScheduler default ``misfire_grace_time=1`` is unsafe for any
    real recovery scenario: if the worker is busy, the loop is paused,
    or the process restarts within 1s of the scheduled fire instant,
    the job is silently skipped for the entire interval (e.g. the whole
    night for ``nightly_digest``). Production jobs must opt into a
    larger grace window so that scheduler-down recovery actually fires
    the missed run.
    """
    from app.core import scheduler as sched_mod

    sched_mod._reset_for_tests()
    try:
        original_testing = sched_mod._TESTING
        sched_mod._TESTING = True
        try:
            sched_mod.start_scheduler()
            sched = sched_mod.get_scheduler()

            for job_id in (
                "nightly_digest",
                "stall_scan",
                "appointment_reminders",
            ):
                job = sched.get_job(job_id)
                assert job is not None, f"missing production job {job_id}"
                # Pending jobs (scheduler stopped) only have
                # misfire_grace_time set if explicitly passed at
                # add_job time. If absent the scheduler will fill in
                # APScheduler's 1-second default at start — too tight
                # for any real recovery scenario.
                grace = getattr(job, "misfire_grace_time", None)
                assert grace is None or grace >= 30, (
                    f"{job_id} misfire_grace_time={grace!r} — too tight; "
                    "set to >=30s so missed fires actually recover"
                )
                assert grace is not None, (
                    f"{job_id} did not opt out of the 1-second default"
                )
        finally:
            sched_mod._TESTING = original_testing
    finally:
        sched_mod._reset_for_tests()
