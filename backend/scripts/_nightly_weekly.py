"""Sunday-only weekly review dispatch (T12.22a) — spoke for nightly_digest.

Builds the per-session weekly review and dispatches it through the same
``send_digest`` path as the daily digest so cooldown + opt-out +
kill-switch gating apply uniformly. Failures are isolated — the daily
digest's accounting must NOT be poisoned by a weekly hiccup.

The send callable is injected (not imported) so tests can monkeypatch
``scripts.nightly_digest.send_digest`` at the orchestrator boundary
without needing to know about this spoke.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

from app.modules.plan import weekly_review

logger = logging.getLogger(__name__)


def send_weekly_review(
    session_id: str,
    email: str,
    for_date: date,
    *,
    db_path: Path,
    send_fn: Callable,
) -> None:
    """Build + dispatch one session's weekly review on a Sunday run.

    The window is the 7 days ending at ``for_date`` (inclusive on both
    ends). Subject is ``"Your week — <start> to <end>"`` so the daily
    digest and the weekly are visually distinct in the inbox.

    ``send_fn`` matches ``reminder_engine.send_digest``'s signature:
    ``(session_id, to_email, subject, html, text, *, db_path, now=None)``.
    """
    try:
        window_start = for_date - timedelta(days=7)
        review = weekly_review.build_weekly_review(
            session_id, (window_start, for_date), db_path=db_path,
        )
        subject = (
            f"Your week — {review.window_start.isoformat()} to "
            f"{review.window_end.isoformat()}"
        )
        send_fn(
            session_id, email, subject,
            review.summary_markdown, review.summary_markdown,
            db_path=db_path,
        )
    except Exception:  # noqa: BLE001 — isolation: weekly must not poison daily
        logger.exception(
            "weekly review failed for session_id=%s — daily digest already sent",
            session_id,
        )


__all__ = ["send_weekly_review"]
