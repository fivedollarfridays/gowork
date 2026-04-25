"""Tests for the fake-clock harness (T13.5).

Covers:
- ``freeze_time(iso_str)`` freezes ``datetime.now(tz)`` for any caller
- ``advance_time(seconds)`` moves the frozen clock forward
- Tear-down restores real wall-clock after the context exits
- APScheduler integration: jobs whose ``next_fire_time`` falls into the past
  after ``advance_time`` actually fire when ``fire_pending(scheduler)`` runs
- Weekly cron (``Sun 23:59``) acceptance scenario: cross the boundary, fire

The harness lives at ``backend/tests/_fake_clock.py``. Underscore-prefixed so
pytest does not collect it as a test module.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tests import _fake_clock as fc


# ---------------------------------------------------------------- freeze_time


def test_freeze_time_freezes_datetime_now() -> None:
    """``datetime.now(tz)`` returns the frozen value while inside the ctx."""
    target = datetime(2026, 4, 19, 12, 30, 0, tzinfo=timezone.utc)
    with fc.freeze_time("2026-04-19T12:30:00+00:00"):
        assert datetime.now(timezone.utc) == target


def test_freeze_time_restores_real_clock_on_exit() -> None:
    """After the context exits, ``datetime.now`` returns wall-clock again."""
    before = datetime.now(timezone.utc)
    with fc.freeze_time("2020-01-01T00:00:00+00:00"):
        assert datetime.now(timezone.utc).year == 2020
    after = datetime.now(timezone.utc)
    # Must have moved past `before` (within the test runtime; hours suffice).
    assert after >= before
    assert after.year != 2020


def test_freeze_time_works_for_naive_now() -> None:
    """``datetime.now()`` (naive) is also frozen."""
    with fc.freeze_time("2026-04-19T12:30:00+00:00"):
        # Naive now() returns local time of the frozen instant; the year
        # is what matters for "is it really frozen?".
        assert datetime.now().year == 2026


# ---------------------------------------------------------------- advance_time


def test_advance_time_moves_clock_forward() -> None:
    """``advance_time(60)`` shifts ``datetime.now`` by 60 seconds."""
    with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
        start = datetime.now(timezone.utc)
        clock.advance(60)
        end = datetime.now(timezone.utc)
        assert (end - start).total_seconds() == 60


def test_advance_time_accepts_timedelta() -> None:
    """``advance(timedelta(...))`` also works."""
    with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
        start = datetime.now(timezone.utc)
        clock.advance(timedelta(hours=2, minutes=30))
        end = datetime.now(timezone.utc)
        assert (end - start) == timedelta(hours=2, minutes=30)


def test_move_to_jumps_to_iso_string() -> None:
    """``move_to`` sets the clock to an arbitrary ISO instant."""
    with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
        clock.move_to("2026-12-31T23:59:59+00:00")
        now = datetime.now(timezone.utc)
        assert now.year == 2026 and now.month == 12 and now.day == 31


# ---------------------------------------------------------------- APScheduler


def test_advance_fires_pending_apscheduler_job() -> None:
    """A job scheduled 60s in the future fires after advance_time(60).

    The scheduler is never started — the harness fires triggers
    synchronously by walking ``scheduler.get_jobs()``, so the production
    APScheduler thread never runs. Test bodies stay deterministic.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.date import DateTrigger

    fired: list[str] = []

    with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
        sched = BackgroundScheduler(timezone=timezone.utc)
        run_at = datetime(2026, 4, 19, 12, 0, 30, tzinfo=timezone.utc)
        sched.add_job(
            lambda: fired.append("hit"),
            trigger=DateTrigger(run_date=run_at, timezone=timezone.utc),
            id="probe",
        )
        # Job is in the future; should not have fired yet.
        assert fired == []
        # Advance 60 seconds — past the run_at instant.
        clock.advance(60, scheduler=sched)
        assert fired == ["hit"]


def test_weekly_cron_triggers_after_sunday_2359(monkeypatch) -> None:
    """Cron `Sun 23:59` fires once we cross the boundary via advance_time.

    Acceptance scenario from T13.5: "after 23:59 on Sunday, weekly review
    triggers".
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    fired: list[datetime] = []

    # Start at Sunday 23:58 UTC (2026-04-19 is a Sunday).
    with fc.freeze_time("2026-04-19T23:58:00+00:00") as clock:
        sched = BackgroundScheduler(timezone=timezone.utc)
        sched.add_job(
            lambda: fired.append(datetime.now(timezone.utc)),
            trigger=CronTrigger(
                day_of_week="sun", hour=23, minute=59, timezone=timezone.utc,
            ),
            id="weekly_review",
        )
        assert fired == []
        # Advance 2 minutes — crosses 23:59.
        clock.advance(120, scheduler=sched)
        assert len(fired) == 1, "weekly_review should have fired exactly once"


# ---------------------------------------------------------------- error paths


def test_clock_outside_context_raises() -> None:
    """Calling ``advance`` after the context has exited raises RuntimeError."""
    with fc.freeze_time("2026-04-19T12:00:00+00:00") as clock:
        pass
    with pytest.raises(RuntimeError):
        clock.advance(1)


def test_freeze_time_accepts_datetime_object() -> None:
    """Pass a ``datetime`` directly instead of an ISO string."""
    instant = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)
    with fc.freeze_time(instant):
        assert datetime.now(timezone.utc) == instant
