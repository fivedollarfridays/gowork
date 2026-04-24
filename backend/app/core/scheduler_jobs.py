"""APScheduler job handler factories (spoke of :mod:`app.core.scheduler`).

Each function in this module is a thin factory that returns the
callable APScheduler will invoke when the trigger fires. Keeping them
here lets :mod:`app.core.scheduler` stay under the project's
``max_functions_per_file`` ceiling while still allowing lazy imports of
heavy handler dependencies.
"""

from __future__ import annotations

import asyncio
from typing import Callable


def nightly_digest_handler() -> Callable:
    """Return the nightly digest job function, imported lazily.

    Avoids pulling the digest stack (retro + compose + SendGrid) at
    app startup — the handler is only referenced when the cron fires.
    """
    from scripts.nightly_digest import nightly_digest_job

    return nightly_digest_job


def appointment_reminders_handler() -> Callable:
    """Return the async handler for the 6h appointment-reminder scan.

    APScheduler's ``AsyncIOScheduler`` awaits coroutines, so the inner
    ``_run`` is ``async def``. The reminder scanner itself is sync
    (sqlite + SendGrid HTTP), so we offload it to the default executor
    via :func:`asyncio.to_thread` to avoid blocking the event loop for
    the full scan duration. DB path resolution happens at run-time so
    tests can monkeypatch
    :func:`app.routes._appointments_helpers.resolve_db_path`.
    """
    async def _run() -> None:
        from app.modules.appointments import transactional_emails
        from app.routes._appointments_helpers import resolve_db_path

        db_path = resolve_db_path()
        await asyncio.to_thread(
            transactional_emails.scan_and_send_reminders, db_path=db_path,
        )

    _run.__name__ = "appointment_reminders_handler"
    return _run


__all__ = ["appointment_reminders_handler", "nightly_digest_handler"]
