"""Past-appointment auto-advance (T12.25a, S12b).

Port of ``ops:lib/nightly_reconcile.py`` adapted to MontGoWork's
SQLite-backed schema (m002 ``appointments`` table) and the S12 engagement
event bus. Sweeps active sessions and, for each appointment whose
``starts_at`` is past plus a 6-hour grace window AND still in
``SCHEDULED`` status, transitions it to ``MISSED`` automatically.

Side effects per advance
------------------------
1. Status flipped via ``scheduler.mark_missed`` (validates transition,
   emits ``appointment.missed`` for the existing outcomes_listener).
2. Audit row written to
   ``engagement_events(category='appointment_auto_advance',
   payload={appointment_id, reason})`` for the operations log.
3. One-time worker notice row written to
   ``engagement_events(category='appointment_auto_missed_notice',
   payload={appointment_id})``. The next daily digest surfaces this
   to the worker with an "I actually attended" correction CTA so they
   can self-correct without us hammering them with stall reminders.
4. Outcome record appended via ``OutcomeTracker.record_outcome`` with
   ``signal_type='appointment_auto_advance'`` — the existing T12.18
   stall detector unconditionally filters this signal type so the
   worker's stall classification stays pinned to their REAL last
   activity (no false "fresh activity" credit from the system itself).

Idempotency
-----------
Both ``reconcile_session_appointments`` and ``advance_past_bookings``
are safe to re-run. The status transition matrix in
``status_transitions.py`` rejects ``MISSED → MISSED``, so the second
sweep iteration finds the row already terminal and skips it before
emitting any duplicate audit/notice rows.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.integrations.email.core import log_engagement_event
from app.modules.appointments import persistence, scheduler
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import AppointmentStatus
from app.modules.outcomes.tracker import OutcomeTracker
from app.modules.outcomes.types import OutcomeRecord

__all__ = [
    "DEFAULT_GRACE_HOURS",
    "ReconcileResult",
    "advance_past_bookings",
    "reconcile_session_appointments",
]

logger = logging.getLogger(__name__)

DEFAULT_GRACE_HOURS = 6
_AUDIT_CATEGORY = "appointment_auto_advance"
_NOTICE_CATEGORY = "appointment_auto_missed_notice"
_OUTCOME_SIGNAL_TYPE = "appointment_auto_advance"
_REASON_PAST_GRACE = "starts_at past + 6h grace; still scheduled"


@dataclass(frozen=True)
class ReconcileResult:
    """Outcome of a single reconcile pass (per-session or sweep-wide)."""

    advanced: int


def _should_advance(
    appt: Appointment, grace: timedelta, now: datetime,
) -> bool:
    """Return True when ``appt`` is past the grace window and still scheduled.

    Mirrors the legacy ``ops:lib/nightly_reconcile._should_advance`` shape
    with two adaptations: SQLAlchemy/SQLite types instead of Zoho dicts,
    and a single ADVANCEABLE state (``SCHEDULED``) instead of the
    {``booked``, ``confirmed``} pair the Zoho integration carried.
    """
    if appt.status is not AppointmentStatus.SCHEDULED:
        return False
    if appt.starts_at is None:
        return False
    return appt.starts_at + grace < now


def _record_advance_artifacts(
    appt: Appointment, *, db_path: str | Path,
) -> None:
    """Write audit + worker notice engagement_events and outcome record."""
    db_p = Path(str(db_path))
    payload = {"appointment_id": appt.id, "reason": _REASON_PAST_GRACE}
    log_engagement_event(
        db_p, session_id=appt.session_id,
        category=_AUDIT_CATEGORY, payload=payload,
    )
    log_engagement_event(
        db_p, session_id=appt.session_id,
        category=_NOTICE_CATEGORY,
        payload={"appointment_id": appt.id},
    )
    tracker = OutcomeTracker(db_path)
    tracker.record_outcome(OutcomeRecord(
        session_id=appt.session_id,
        signal_type=_OUTCOME_SIGNAL_TYPE,
        resource_ratings={},
    ))


def _advance_one(
    appt: Appointment, *, db_path: str | Path,
) -> bool:
    """Mark ``appt`` missed and write all advance artifacts. Returns True on success.

    Errors are logged + swallowed so a single broken row can't take down
    the sweep — matches the legacy reconcile's "skip, log, continue"
    contract.
    """
    try:
        scheduler.mark_missed(appt.id, db_path=db_path)
    except Exception:  # noqa: BLE001 — sweep robustness over per-row strictness
        logger.exception(
            "auto-advance failed: appointment_id=%s session_id=%s",
            appt.id, appt.session_id,
        )
        return False
    _record_advance_artifacts(appt, db_path=db_path)
    return True


def reconcile_session_appointments(
    session_id: str,
    *,
    db_path: str | Path,
    now: datetime | None = None,
    grace_hours: int = DEFAULT_GRACE_HOURS,
) -> ReconcileResult:
    """Auto-advance every overdue scheduled appointment for one session."""
    resolved_now = now or datetime.now(timezone.utc)
    grace = timedelta(hours=grace_hours)
    rows = persistence.select_by_session(session_id, db_path=db_path)
    advanced = 0
    for appt in rows:
        if not _should_advance(appt, grace, resolved_now):
            continue
        if _advance_one(appt, db_path=db_path):
            advanced += 1
    return ReconcileResult(advanced=advanced)


def _active_session_ids(
    db_path: str | Path, now: datetime,
) -> list[str]:
    """Return session IDs whose ``expires_at`` is still in the future.

    Mirrors the active-session definition in ``stall_detector`` so both
    nightly sweeps see the same population of workers.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id FROM sessions "
            "WHERE expires_at IS NULL OR datetime(expires_at) > datetime(?)",
            (now.isoformat(),),
        ).fetchall()
    finally:
        conn.close()
    return [sid for (sid,) in rows]


def advance_past_bookings(
    *,
    db_path: str | Path,
    now: datetime | None = None,
    grace_hours: int = DEFAULT_GRACE_HOURS,
) -> ReconcileResult:
    """Sweep all active sessions and auto-advance their overdue appointments.

    ``grace_hours`` defaults to ``DEFAULT_GRACE_HOURS`` (6) — the value
    the spec calls for; bumped from the legacy 30-minute Zoho threshold
    because worker-entered appointments need wider tolerance for late
    self-marking ("I went, I just haven't logged it yet").
    """
    resolved_now = now or datetime.now(timezone.utc)
    total = 0
    for session_id in _active_session_ids(db_path, resolved_now):
        result = reconcile_session_appointments(
            session_id, db_path=db_path,
            now=resolved_now, grace_hours=grace_hours,
        )
        total += result.advanced
    return ReconcileResult(advanced=total)
