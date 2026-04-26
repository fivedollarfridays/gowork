"""Fake-clock harness for time-dependent tests (T13.5).

Why this module exists
======================

Roughly 70 production call sites read wall-clock time via
``datetime.now(timezone.utc)`` or ``datetime.utcnow()`` (token TTLs,
cooldowns, stall detection, weekly-review windows, scheduled jobs).
Tests that exercise those paths are flaky because the assertion data is
captured at import time but the production code reads time at call time.
The recent ``_NOW = datetime.now(timezone.utc)`` workaround in
``test_compliance.py`` is the symptom — this harness is the fix.

Approach
========

We use ``freezegun.freeze_time`` under the hood. Why third-party rather
than rolling our own:

* The codebase does NOT centralize ``now()`` in a single helper, so
  monkeypatching one helper would not catch most call sites.
* Rolling our own would have to subclass ``datetime.datetime`` and
  inject the subclass into every importing module — exactly what
  ``freezegun`` already does, with seven years of edge-case fixes.
* APScheduler reads time via ``datetime.now(self.timezone)`` in its
  triggers and scheduler base class; ``freezegun`` patches the
  ``datetime`` module those imports resolve, so APScheduler trigger
  evaluation respects the frozen clock automatically.

Public API
==========

``freeze_time(instant)`` — context manager. Accepts an ISO 8601 string
or a ``datetime`` object. Yields a :class:`FrozenClock` controller.

``FrozenClock.advance(seconds_or_timedelta, scheduler=None)`` — moves
the frozen clock forward. If a ``BackgroundScheduler`` is passed, any
job whose ``next_fire_time`` falls into the past after the advance is
fired synchronously (in-thread).

``FrozenClock.move_to(instant)`` — jump to an arbitrary instant.

``FrozenClock.fire_pending(scheduler)`` — fire any pending jobs without
moving the clock (useful when you've already advanced via ``move_to``).

What this is NOT
================

* Not for use in production code — import only from ``tests/``.
* Not a replacement for unit-testing helpers that already accept
  ``now=`` kwargs (e.g. ``tokens.sign(..., now=...)``); those are still
  preferred for tightly-scoped expiry tests. Use this harness when the
  call site does not expose ``now=`` injection or when multiple call
  sites must agree on "what time is it".
"""
from __future__ import annotations

import contextlib
from datetime import datetime, timedelta, timezone
from typing import Iterator

from freezegun import freeze_time as _freezegun_freeze_time
from freezegun.api import FrozenDateTimeFactory


class FrozenClock:
    """Controller object yielded by :func:`freeze_time`.

    Wraps the freezegun factory and adds APScheduler integration.
    """

    def __init__(self, factory: FrozenDateTimeFactory) -> None:
        self._factory: FrozenDateTimeFactory | None = factory

    def _check_active(self) -> FrozenDateTimeFactory:
        if self._factory is None:
            raise RuntimeError(
                "FrozenClock used outside its freeze_time context manager",
            )
        return self._factory

    def advance(
        self,
        amount: float | timedelta,
        scheduler: object | None = None,
    ) -> None:
        """Move the frozen clock forward by ``amount``.

        ``amount`` is a number of seconds (int/float) or a ``timedelta``.
        If ``scheduler`` is provided it must be an APScheduler-compatible
        scheduler instance; any jobs whose trigger would have fired between
        the previous instant and the new instant are executed synchronously.
        """
        factory = self._check_active()
        delta = amount if isinstance(amount, timedelta) else timedelta(
            seconds=amount,
        )
        start = datetime.now(timezone.utc)
        factory.tick(delta=delta)
        if scheduler is not None:
            self._fire_window(scheduler, start)

    def move_to(self, instant: str | datetime, scheduler: object | None = None) -> None:
        """Jump the frozen clock to an arbitrary instant.

        If ``scheduler`` is provided, jobs that would have fired between
        the previous instant and ``instant`` are executed synchronously.
        """
        factory = self._check_active()
        start = datetime.now(timezone.utc)
        factory.move_to(instant)
        if scheduler is not None:
            self._fire_window(scheduler, start)

    def fire_pending(self, scheduler: object) -> None:
        """Fire any jobs whose next-fire time is at or before the current frozen instant.

        Useful when the test moved the clock without going through this
        controller (e.g. by calling ``move_to`` on the underlying
        freezegun factory directly), or when a job was added after the
        last advance.
        """
        self._check_active()
        # Use a far-past anchor so any job that should have already fired
        # by 'now' is caught, regardless of when we last advanced.
        anchor = datetime(1970, 1, 1, tzinfo=timezone.utc)
        self._fire_window(scheduler, anchor)

    def _fire_window(self, scheduler: object, start: datetime) -> None:
        """Fire jobs whose triggers would have fired in (start, now]."""
        end = datetime.now(timezone.utc)
        jobs = scheduler.get_jobs()  # type: ignore[attr-defined]
        for job in jobs:
            _fire_job_in_window(job, start, end)

    # Internal — called by the context-manager teardown.
    def _deactivate(self) -> None:
        self._factory = None


def _fire_job_in_window(job: object, start: datetime, end: datetime) -> None:
    """Fire ``job`` for every trigger fire-time in the half-open window (start, end].

    Walks the trigger sequentially: ask for the first fire after ``start``,
    fire if it falls at or before ``end``, then ask for the fire after
    that one, and so on. This handles intervals/crons that would have
    fired multiple times during a long advance.
    """
    trigger = job.trigger  # type: ignore[attr-defined]
    next_fire = trigger.get_next_fire_time(None, start)
    while next_fire is not None and next_fire <= end:
        job.func(*job.args, **job.kwargs)  # type: ignore[attr-defined]
        # Ask "what's the next fire strictly after the one we just ran?"
        next_fire = trigger.get_next_fire_time(next_fire, next_fire)


@contextlib.contextmanager
def freeze_time(instant: str | datetime) -> Iterator[FrozenClock]:
    """Context manager that freezes ``datetime.now`` to ``instant``.

    ``instant`` is an ISO 8601 string (preferred — explicit timezone) or
    a timezone-aware ``datetime`` object. UTC is assumed if a naive
    datetime is passed; this matches the project's convention of
    storing all timestamps in UTC.
    """
    target = _coerce_to_datetime(instant)
    with _freezegun_freeze_time(target) as factory:
        clock = FrozenClock(factory)
        try:
            yield clock
        finally:
            clock._deactivate()


def _coerce_to_datetime(instant: str | datetime) -> datetime:
    """Normalize the ``instant`` argument to a tz-aware ``datetime``."""
    if isinstance(instant, datetime):
        return instant if instant.tzinfo else instant.replace(
            tzinfo=timezone.utc,
        )
    # ISO string — let datetime parse it.
    parsed = datetime.fromisoformat(instant)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


__all__ = ["FrozenClock", "freeze_time"]
