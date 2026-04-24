"""Nightly orchestrator — S12a worker companion digest pipeline (T12.25).

Runs at 02:00 city-local via APScheduler. For every active session in the
targeted city:

1. Run yesterday's retro (T12.22).
2. Compute stall signals (T12.18) — included in the digest via
   :func:`compose_digest` which calls the detector internally.
3. Refresh the plan — **stubbed** for S12a; real implementation lands in
   S12b T12.24.
4. Compose the daily digest (T12.20).
5. Dispatch the digest through the reminder engine (T12.19) —
   :func:`reminder_engine.send_digest` gates the SendGrid call behind
   the (session_id, "digest") cooldown, the ``reminders_auto_disabled``
   engagement_events opt-out row (worker opt-out OR T12.2a hard-bounce),
   and the ``EMAIL_SEND_ENABLED`` kill switch, then logs an
   ``engagement_events`` row on success.

Kill switch
-----------
Short-circuited by the ``FEATURE_NIGHTLY_ENABLED`` flag (T12.0b,
default True). When off we log and return without touching the DB.

City-scope enforcement
----------------------
The ``sessions`` table has no ``city`` column (m001). This
orchestrator uses ``outcomes_records.payload_json.city`` as the
canonical per-session city tag — matching the T12.12 outcomes model.
A session is processed for a city only when it has at least one
outcomes row tagging that city. Sessions with no city tag are
considered unscoped and are skipped by city-scoped runs; a future
S12b ticket can add a dedicated ``sessions.city`` column for cheap
enforcement without the outcomes scan.

Concurrency
-----------
Cities are iterated sequentially; sessions within a city run
concurrently behind ``asyncio.Semaphore(10)``. Per-session errors are
caught + counted; they do NOT abort the batch.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from app.core import day_boundary, feature_flags
from app.modules.appointments.reconcile import reconcile_session_appointments
from app.modules.common.temporal_types import TIMEZONE_BY_CITY
from app.modules.engagement.digest_composer import compose_digest
from app.modules.engagement.reminder_engine import send_digest
# ``weekly_review`` and ``plan_refresher`` stay as module attributes (not
# just names) so tests can monkeypatch ``nd.weekly_review.build_weekly_review``
# and ``nd.refresh_plan`` directly. T12.24 added plan_refresher here.
from app.modules.plan import (
    daily_progress as _daily_progress_mod,
    plan_refresher as _plan_refresher_mod,
    weekly_review,
)

refresh_plan = _plan_refresher_mod.refresh_plan
run_nightly_retro = _daily_progress_mod.run_nightly_retro
from scripts import _nightly_db, _nightly_weekly
from scripts.nightly_accounting import RunAccounting, insert_run_row, url_to_path

logger = logging.getLogger(__name__)

_SESSION_CONCURRENCY = 10
_FLAG = "FEATURE_NIGHTLY_ENABLED"


@dataclass(frozen=True)
class SessionOutcome:
    """Per-session orchestration result."""

    session_id: str
    city: str
    email_sent: bool
    error: str | None


def _reconcile_session(session_id: str, db_path: Path, now: datetime) -> None:
    """T12.25a step 2.5 — auto-advance overdue appointments past 6h grace.

    Runs between retro (step 2) and plan refresh (step 3). Failures are
    logged but never propagate so a single broken session can't abort
    the digest pipeline (matches the T12.24 robustness contract).
    """
    try:
        reconcile_session_appointments(
            session_id, db_path=db_path, now=now,
        )
    except Exception:  # noqa: BLE001 — reconcile must never block the digest
        logger.exception(
            "appointment reconcile failed for session_id=%s; continuing",
            session_id,
        )


def _refresh_session_plan(session_id: str, db_path: Path, now: datetime) -> None:
    """T12.24 plan-refresh slot — invokes the refresher with auto-detect.

    The refresher itself is a no-op when neither HARD stall nor a recent
    breakthrough is present; we still call it on every session so the
    detection runs in one place. Failures are logged but never propagate
    so a single buggy session can't abort the digest pipeline.
    """
    try:
        refresh_plan(session_id, db_path=db_path, now=now)
    except Exception:  # noqa: BLE001 — refresh must never block the digest
        logger.exception(
            "plan refresh failed for session_id=%s; continuing", session_id,
        )


async def _process_session(
    session_id: str, city: str, for_date: date, db_path: Path, now: datetime,
) -> SessionOutcome:
    """Run the retro → plan-refresh → compose → send pipeline for one session.

    Any per-session exception propagates up; the caller is responsible
    for catching and tallying it as an error (keeps this function focused).
    """
    run_nightly_retro(session_id, for_date, db_path=db_path)
    _reconcile_session(session_id, db_path, now)
    _refresh_session_plan(session_id, db_path, now)
    digest = compose_digest(
        session_id, for_date, db_path=db_path, city=city,
    )
    email = _nightly_db.resolve_session_email(session_id, db_path)
    if email is None:
        logger.warning(
            "skipping send for %s: session has no email in profile",
            session_id,
        )
        return SessionOutcome(
            session_id=session_id, city=city, email_sent=False, error=None,
        )
    sent_ok = _dispatch_daily(session_id, email, digest, db_path=db_path)
    # T12.22a — Sunday-only weekly review piggybacks on the same send path
    # so cooldown + opt-out gating apply uniformly. Weekday() == 6 is Sunday
    # in Python's convention; the caller-supplied ``now`` lets tests pin the
    # day deterministically.
    if now.weekday() == 6:
        _nightly_weekly.send_weekly_review(
            session_id, email, for_date,
            db_path=db_path, send_fn=send_digest,
        )
    return SessionOutcome(
        session_id=session_id, city=city,
        email_sent=sent_ok, error=None,
    )


def _dispatch_daily(
    session_id: str, email: str, digest, *, db_path: Path,
) -> bool:
    """Send the daily digest through reminder_engine and return success.

    T12.19 — every nightly send is gated on the (session_id, "digest")
    cooldown, the engagement_events ``reminders_auto_disabled`` opt-out
    row (worker opt-out OR T12.2a hard-bounce), and the
    EMAIL_SEND_ENABLED kill switch. The engine logs engagement_events on
    success; we only tally the accounting outcome here.
    """
    result = send_digest(
        session_id, email, digest.subject, digest.html, digest.text,
        db_path=db_path,
    )
    return bool(result.success)


async def _run_one(
    sem: asyncio.Semaphore,
    session_id: str,
    city: str,
    for_date: date,
    db_path: Path,
    now: datetime,
) -> SessionOutcome:
    """Semaphore-bounded wrapper that converts exceptions into SessionOutcomes."""
    async with sem:
        try:
            return await _process_session(
                session_id, city, for_date, db_path, now,
            )
        except Exception as exc:  # noqa: BLE001 — broad by design (isolation)
            logger.exception(
                "nightly session failed: session_id=%s city=%s", session_id, city,
            )
            return SessionOutcome(
                session_id=session_id, city=city,
                email_sent=False, error=f"{type(exc).__name__}: {exc}",
            )


async def _process_city(
    city: str, db_path: Path, now: datetime,
) -> RunAccounting:
    """Process every active session for ``city`` and write an accounting row."""
    start = datetime.now(timezone.utc)
    sessions = _nightly_db.collect_active_sessions_for_city(
        city, db_path, now,
    )
    for_date = day_boundary.current_work_date(city, now=now)
    sem = asyncio.Semaphore(_SESSION_CONCURRENCY)
    outcomes = await asyncio.gather(
        *(
            _run_one(sem, sid, city, for_date, db_path, now)
            for sid in sessions
        ),
    )
    end = datetime.now(timezone.utc)
    acct = RunAccounting(
        city=city,
        sessions_processed=len(outcomes),
        emails_sent=sum(1 for o in outcomes if o.email_sent),
        errors=sum(1 for o in outcomes if o.error is not None),
        duration_sec=(end - start).total_seconds(),
        start_ts=start,
        end_ts=end,
    )
    insert_run_row(db_path, acct)
    logger.info(
        "nightly digest city=%s processed=%d sent=%d errors=%d duration=%.2fs",
        acct.city, acct.sessions_processed, acct.emails_sent,
        acct.errors, acct.duration_sec,
    )
    return acct


async def run_nightly_digest(
    *,
    cities: list[str] | None = None,
    db_path: str | Path | None = None,
    now: datetime | None = None,
) -> list[RunAccounting]:
    """Orchestrate the nightly digest across the given (or all) cities.

    Returns one :class:`RunAccounting` per city processed. When the
    kill switch is OFF, returns ``[]`` without touching the DB.
    """
    if not feature_flags.is_enabled(_FLAG, default=True):
        logger.info("nightly digest disabled via feature flag, skipping")
        return []
    if db_path is None:
        # Import settings lazily only when the handler is invoked without an
        # explicit path — avoids pulling pydantic-settings at module import.
        from app.core.config import get_settings  # noqa: PLC0415
        resolved_db = url_to_path(get_settings().database_url)
    else:
        resolved_db = Path(db_path)
    resolved_now = now or datetime.now(timezone.utc)
    target_cities = cities if cities is not None else list(TIMEZONE_BY_CITY)
    results: list[RunAccounting] = []
    for city in target_cities:
        results.append(await _process_city(city, resolved_db, resolved_now))
    return results


async def nightly_digest_job() -> None:
    """APScheduler-compatible async entrypoint (registered in scheduler.py)."""
    await run_nightly_digest()


__all__ = [
    "RunAccounting",
    "SessionOutcome",
    "nightly_digest_job",
    "run_nightly_digest",
]
