"""APScheduler singleton + job registration helpers (T12.3).

S12a scope: single-worker in-process via `WEB_CONCURRENCY=1` hard constraint
(scheduler_leases lock deferred to S13). Three jobs registered at startup as
no-op stubs — real handlers land in later tasks. AsyncIOScheduler is used
because FastAPI's lifespan runs inside the asyncio loop. All S12a cron jobs
use America/Chicago (both cities are Central); per-city timezones arrive when
handlers need to differentiate.
"""

from __future__ import annotations

import logging
import os
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# All S12a cron jobs run in CT (both cities are Central).
_SCHEDULER_TZ = "America/Chicago"

_scheduler: AsyncIOScheduler | None = None

# Set to True by the test suite (conftest.py or per-test) to skip the
# `scheduler.start()` call — AsyncIOScheduler requires a running event loop,
# which synchronous unit tests don't have. Job registration still runs so
# tests can assert on `scheduler.get_jobs()`.
_TESTING: bool = False


def get_scheduler() -> AsyncIOScheduler:
    """Return the module-level scheduler singleton, creating it if needed."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=_SCHEDULER_TZ)
    return _scheduler


def register_job(
    name: str,
    func: Callable,
    trigger,
    *,
    misfire_grace_time: int = 300,
) -> None:
    """Register `func` under job id `name` with the given trigger.

    Replaces any existing job with the same id so startup is idempotent.

    ``misfire_grace_time`` (seconds) overrides the APScheduler default
    of 1 second, which is too tight to recover any job that misses its
    fire window because of a worker restart or a busy event loop. The
    default of 300s (5 minutes) is a sensible floor for daily cron
    jobs; per-job overrides are accepted via the keyword argument.
    """
    sched = get_scheduler()
    sched.add_job(
        func,
        trigger=trigger,
        id=name,
        replace_existing=True,
        misfire_grace_time=misfire_grace_time,
    )


def enforce_single_worker() -> None:
    """Raise RuntimeError unless `WEB_CONCURRENCY` is "1" or unset.

    In-process APScheduler duplicates every scheduled job when multiple
    workers are spawned. Until we adopt the `scheduler_leases` distributed
    lock (S13), single-worker is a hard constraint.
    """
    value = os.environ.get("WEB_CONCURRENCY", "1")
    if value != "1":
        raise RuntimeError(
            "APScheduler in-process requires WEB_CONCURRENCY=1 "
            f"(got {value!r}); use a distributed runner for multi-worker"
        )


def _make_stub(job_name: str, note: str) -> Callable[[], None]:
    """Build a no-op job handler that logs a TODO when fired."""
    def _stub() -> None:
        logger.info("TODO: %s handler (%s)", job_name, note)
    _stub.__name__ = f"{job_name}_stub"
    return _stub


def _register_default_jobs() -> None:
    """Register the three S12a recurring jobs (T12.25 wires nightly_digest).

    Per-job ``misfire_grace_time`` (seconds): wide enough to absorb a
    worker restart but narrow enough that a stale fire is still useful
    work. 5 minutes for daily crons, 30 minutes for the 6h appointment
    reminder scan.
    """
    from app.core import scheduler_jobs

    register_job(
        "nightly_digest",
        scheduler_jobs.nightly_digest_handler(),
        CronTrigger(hour=2, minute=0, timezone=_SCHEDULER_TZ),
        misfire_grace_time=300,
    )
    register_job(
        "stall_scan",
        _make_stub("stall_scan", "later S12a task"),
        CronTrigger(hour=8, minute=0, timezone=_SCHEDULER_TZ),
        misfire_grace_time=300,
    )
    register_job(
        "appointment_reminders",
        scheduler_jobs.appointment_reminders_handler(),
        IntervalTrigger(hours=6),
        misfire_grace_time=1800,
    )


def start_scheduler() -> None:
    """Register default jobs and start the scheduler (idempotent).

    When `_TESTING` is True (set by the test suite), registers jobs but
    skips `sched.start()` — AsyncIOScheduler requires a running loop we
    don't have inside synchronous test bodies.
    """
    sched = get_scheduler()
    _register_default_jobs()
    if _TESTING:
        return
    if not sched.running:
        sched.start()


def shutdown_scheduler(wait: bool = False) -> None:
    """Stop the scheduler if running; safe to call multiple times."""
    global _scheduler
    if _scheduler is None:
        return
    if _scheduler.running:
        _scheduler.shutdown(wait=wait)


def scheduler_state_summary() -> str:
    """One-line startup-log summary: running flag + job count + tz."""
    sched = get_scheduler()
    job_count = len(sched.get_jobs())
    state = "running" if sched.running else "stopped"
    return f"scheduler={state} jobs={job_count} tz={_SCHEDULER_TZ}"


def _reset_for_tests() -> None:
    """Reset the module singleton so tests start from a clean scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None


__all__ = [
    "enforce_single_worker",
    "get_scheduler",
    "register_job",
    "scheduler_state_summary",
    "shutdown_scheduler",
    "start_scheduler",
]
