"""Tests for app.core.scheduler_jobs handler factories.

S1 fix: appointment_reminders_handler must offload the synchronous
scan_and_send_reminders call to a worker thread (via asyncio.to_thread)
so the AsyncIOScheduler event loop is not blocked for the duration of
the scan (sqlite + SendGrid HTTP can take seconds).
"""

from __future__ import annotations

import asyncio
import inspect
import threading

import pytest


def test_appointment_reminders_handler_returns_coroutine_factory() -> None:
    """Factory returns a coroutine function APScheduler can await."""
    from app.core import scheduler_jobs

    handler = scheduler_jobs.appointment_reminders_handler()
    assert inspect.iscoroutinefunction(handler)
    assert handler.__name__ == "appointment_reminders_handler"


def test_appointment_reminders_handler_offloads_to_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The sync scanner must run on a thread other than the event-loop thread.

    Regression guard for S1: previously the handler called the sync
    scanner directly, blocking the event loop for the full scan duration.
    The fix wraps the call in asyncio.to_thread so the running thread is
    not the loop thread.
    """
    from app.core import scheduler_jobs

    captured: dict = {}

    def _fake_scan(*, db_path: str) -> None:
        captured["thread"] = threading.current_thread()
        captured["db_path"] = db_path

    # Monkeypatch the lazy-imported targets the handler references.
    import app.modules.appointments.transactional_emails as te
    monkeypatch.setattr(te, "scan_and_send_reminders", _fake_scan)
    import app.routes._appointments_helpers as helpers
    monkeypatch.setattr(helpers, "resolve_db_path", lambda: "/tmp/test.db")

    handler = scheduler_jobs.appointment_reminders_handler()
    loop = asyncio.new_event_loop()
    try:
        loop_thread_holder: dict = {}

        async def _run() -> None:
            loop_thread_holder["loop_thread"] = threading.current_thread()
            await handler()

        loop.run_until_complete(_run())
    finally:
        loop.close()

    assert captured["db_path"] == "/tmp/test.db"
    # Critical: the scanner must NOT have run on the event-loop thread.
    assert (
        captured["thread"] is not loop_thread_holder["loop_thread"]
    ), "scan_and_send_reminders ran on the event loop — would block it"
