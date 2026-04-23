"""Nightly orchestrator — S12a worker companion digest pipeline (T12.25).

Runs at 02:00 city-local via APScheduler. For every active session in the
targeted city:

1. Run yesterday's retro (T12.22).
2. Compute stall signals (T12.18) — included in the digest via
   :func:`compose_digest` which calls the detector internally.
3. Refresh the plan — **stubbed** for S12a; real implementation lands in
   S12b T12.24.
4. Compose the daily digest (T12.20).
5. Send via SendGrid (T12.2) directly. **TODO S12b T12.19**: route
   through the reminder engine with cooldown/dedup instead.

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
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from app.core import day_boundary, feature_flags
from app.integrations.email.sendgrid_client import send_transactional
from app.modules.common.temporal_types import TIMEZONE_BY_CITY
from app.modules.engagement.digest_composer import compose_digest
from app.modules.plan.daily_progress import run_nightly_retro
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


def _collect_active_sessions_for_city(
    city: str, db_path: Path, now: datetime,
) -> list[str]:
    """Return session IDs active at ``now`` and tagged to ``city``.

    "Active" = ``expires_at`` > now OR NULL. "Tagged to city" = has at
    least one outcomes_records row whose payload_json.city == city.
    See module docstring for the scope-enforcement rationale.
    """
    now_iso = now.isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT DISTINCT s.id FROM sessions s "
            "JOIN outcomes_records o ON o.session_id = s.id "
            "WHERE (s.expires_at IS NULL OR s.expires_at > ?) "
            "AND json_extract(o.payload_json, '$.city') = ?",
            (now_iso, city),
        ).fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def _resolve_session_email(session_id: str, db_path: Path) -> str | None:
    """Pull ``profile.email`` from the sessions row; None if missing."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT profile FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return None
    try:
        profile = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None
    email = profile.get("email") if isinstance(profile, dict) else None
    if isinstance(email, str) and email.strip():
        return email.strip()
    return None


def _plan_refresh_stub(session_id: str) -> None:
    """S12b T12.24 plan-refresh slot — no-op for S12a."""
    logger.debug(
        "nightly plan-refresh skipped for %s — TODO S12b T12.24", session_id,
    )


async def _process_session(
    session_id: str, city: str, for_date: date, db_path: Path,
) -> SessionOutcome:
    """Run the retro → refresh-stub → compose → send pipeline for one session.

    Any per-session exception propagates up; the caller is responsible
    for catching and tallying it as an error (keeps this function focused).
    """
    run_nightly_retro(session_id, for_date, db_path=db_path)
    _plan_refresh_stub(session_id)
    digest = compose_digest(
        session_id, for_date, db_path=db_path, city=city,
    )
    email = _resolve_session_email(session_id, db_path)
    if email is None:
        logger.warning(
            "skipping send for %s: session has no email in profile",
            session_id,
        )
        return SessionOutcome(
            session_id=session_id, city=city, email_sent=False, error=None,
        )
    # TODO S12b T12.19: replace direct SendGrid call with reminder_engine
    #                   (adds cooldown + dedup; respects quiet hours).
    result = send_transactional(
        email, digest.subject, digest.html, digest.text,
        "digest", session_id=session_id, db_path=db_path,
    )
    return SessionOutcome(
        session_id=session_id, city=city,
        email_sent=bool(result.success), error=None,
    )


async def _run_one(
    sem: asyncio.Semaphore,
    session_id: str,
    city: str,
    for_date: date,
    db_path: Path,
) -> SessionOutcome:
    """Semaphore-bounded wrapper that converts exceptions into SessionOutcomes."""
    async with sem:
        try:
            return await _process_session(session_id, city, for_date, db_path)
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
    sessions = _collect_active_sessions_for_city(city, db_path, now)
    for_date = day_boundary.current_work_date(city, now=now)
    sem = asyncio.Semaphore(_SESSION_CONCURRENCY)
    outcomes = await asyncio.gather(
        *(_run_one(sem, sid, city, for_date, db_path) for sid in sessions),
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
