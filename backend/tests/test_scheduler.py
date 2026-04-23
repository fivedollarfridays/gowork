"""Tests for app.core.scheduler (T12.3).

Verifies:
  * register_job adds the job to the module-level scheduler
  * start_scheduler registers the three S12a jobs with correct triggers
  * WEB_CONCURRENCY enforcement raises when >1, allows 1 or unset
  * scheduler_state_summary returns a sane one-liner
"""

from __future__ import annotations

import pytest

from app.core import scheduler as sched_mod


@pytest.fixture(autouse=True)
def _isolate_scheduler(monkeypatch):
    """Stop and reset scheduler singleton between tests + skip real start()."""
    monkeypatch.setattr(sched_mod, "_TESTING", True)
    sched_mod._reset_for_tests()
    yield
    sched_mod._reset_for_tests()


def _noop():
    """Placeholder job handler used in registration tests."""


def test_register_job_adds_to_scheduler():
    """After register_job, scheduler.get_job returns the registered job."""
    from apscheduler.triggers.interval import IntervalTrigger

    sched = sched_mod.get_scheduler()
    sched_mod.register_job("probe_job", _noop, IntervalTrigger(hours=1))
    assert sched.get_job("probe_job") is not None


def test_three_jobs_registered_at_startup():
    """start_scheduler registers nightly_digest, stall_scan, appointment_reminders."""
    sched_mod.start_scheduler()
    sched = sched_mod.get_scheduler()
    for job_id in ("nightly_digest", "stall_scan", "appointment_reminders"):
        assert sched.get_job(job_id) is not None, f"missing job {job_id}"


def test_nightly_digest_cron_0200():
    """nightly_digest cron trigger fires at 02:00."""
    from apscheduler.triggers.cron import CronTrigger

    sched_mod.start_scheduler()
    job = sched_mod.get_scheduler().get_job("nightly_digest")
    assert isinstance(job.trigger, CronTrigger)
    fields = {f.name: str(f) for f in job.trigger.fields}
    assert fields["hour"] == "2"
    assert fields["minute"] == "0"


def test_stall_scan_cron_0800():
    """stall_scan cron trigger fires at 08:00."""
    from apscheduler.triggers.cron import CronTrigger

    sched_mod.start_scheduler()
    job = sched_mod.get_scheduler().get_job("stall_scan")
    assert isinstance(job.trigger, CronTrigger)
    fields = {f.name: str(f) for f in job.trigger.fields}
    assert fields["hour"] == "8"
    assert fields["minute"] == "0"


def test_appointment_reminders_interval_6h():
    """appointment_reminders uses a 6-hour interval trigger."""
    from apscheduler.triggers.interval import IntervalTrigger

    sched_mod.start_scheduler()
    job = sched_mod.get_scheduler().get_job("appointment_reminders")
    assert isinstance(job.trigger, IntervalTrigger)
    assert job.trigger.interval.total_seconds() == 6 * 3600


def test_scheduler_state_summary_returns_string():
    """scheduler_state_summary returns a one-line status with job count."""
    sched_mod.start_scheduler()
    summary = sched_mod.scheduler_state_summary()
    assert isinstance(summary, str)
    assert "3" in summary  # three jobs registered


def test_web_concurrency_not_one_raises(monkeypatch):
    """When WEB_CONCURRENCY=2, enforce_single_worker raises RuntimeError."""
    monkeypatch.setenv("WEB_CONCURRENCY", "2")
    with pytest.raises(RuntimeError, match="WEB_CONCURRENCY=1"):
        sched_mod.enforce_single_worker()


def test_web_concurrency_one_allows(monkeypatch):
    """WEB_CONCURRENCY=1 passes enforce_single_worker."""
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    sched_mod.enforce_single_worker()  # no raise


def test_web_concurrency_unset_allows(monkeypatch):
    """Unset WEB_CONCURRENCY defaults to 1 and passes."""
    monkeypatch.delenv("WEB_CONCURRENCY", raising=False)
    sched_mod.enforce_single_worker()  # no raise


def test_shutdown_scheduler_idempotent():
    """Calling shutdown_scheduler twice does not raise."""
    sched_mod.start_scheduler()
    sched_mod.shutdown_scheduler()
    sched_mod.shutdown_scheduler()  # second call safe
