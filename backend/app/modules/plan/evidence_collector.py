"""Unified evidence bundle for a session over an inclusive date range (T12.23).

Reads progress signals from three already-wired data sources:
  * appointments (T12.7)      — attended / missed statuses
  * job_applications (T12.11) — filed (APPLIED) + progressed transitions
  * outcomes_records (T12.0a) — every event recorded for the session

Inclusive on BOTH ends: a range of `[2026-04-20, 2026-04-20]` (single day)
returns all events stamped on 2026-04-20 regardless of time-of-day. We
convert the end date to `datetime.combine(end, time.max, utc)` so the full
end day is included.

City scope is implicit: `session_id` is FK-bound to `sessions(id)`, so any
signal carrying the same session_id belongs to that session's city.

Checklist note
--------------
The project does not yet expose a structured `progress_checklist` table;
the only checklist storage today is the `sessions.action_checklist` JSON
blob without per-item completion timestamps. We therefore return an empty
`checklist_items_completed` list and leave this TODO for a future migration.
Downstream consumers (retro T12.22, digest T12.20) are expected to tolerate
the empty list.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from pathlib import Path

from pydantic import BaseModel

from app.modules.appointments import scheduler
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import (
    AppointmentStatus,
    JobApplicationStatus,
)
from app.modules.jobs import applications
from app.modules.jobs.types import JobApplication
from app.modules.outcomes.tracker import OutcomeTracker
from app.modules.outcomes.types import OutcomeRecord

# Event types on outcomes_records that indicate forward motion on an
# application. APPLIED itself counts as "filed", not "progressed".
_PROGRESSED_EVENT_TYPES: frozenset[str] = frozenset({
    "job_application_interview",
    "job_application_offer",
})


class EvidenceBundle(BaseModel):
    """Unified progress evidence for a session over a date range.

    All list fields default to empty — a session with zero activity in
    the window still produces a valid (empty) bundle.
    """

    session_id: str
    date_range_start: date
    date_range_end: date
    checklist_items_completed: list[dict] = []
    appointments_attended: list[Appointment] = []
    appointments_missed: list[Appointment] = []
    applications_filed: list[JobApplication] = []
    applications_progressed: list[JobApplication] = []
    outcomes_logged: list[OutcomeRecord] = []


def _end_of_day(d: date) -> datetime:
    """UTC datetime at the final microsecond of day `d` (inclusive end)."""
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


def _start_of_day(d: date) -> datetime:
    """UTC datetime at 00:00:00 of day `d` (inclusive start)."""
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _in_range(dt: datetime | None, start: date, end: date) -> bool:
    """True when dt falls within [start 00:00:00, end 23:59:59.999999] UTC."""
    if dt is None:
        return False
    return _start_of_day(start) <= dt <= _end_of_day(end)


def _date_in_range(d: date | None, start: date, end: date) -> bool:
    """True when d is in [start, end] inclusive. None => False."""
    if d is None:
        return False
    return start <= d <= end


def _parse_iso(value: str | None) -> datetime | None:
    """Parse an ISO-8601 string (possibly ending 'Z') into an aware datetime."""
    if not value:
        return None
    s = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _filter_appointments(
    session_id: str,
    status: AppointmentStatus,
    start: date,
    end: date,
    db_path: str | Path,
) -> list[Appointment]:
    """Return this session's appointments with `status` and starts_at in range."""
    rows = scheduler.list_by_session(session_id, db_path=db_path)
    return [
        a for a in rows
        if a.status == status and _in_range(a.starts_at, start, end)
    ]


def _filter_applied(
    session_id: str, start: date, end: date, db_path: str | Path,
) -> list[JobApplication]:
    """Applications with APPLIED status whose applied_date is in range."""
    rows = applications.list_by_status(
        session_id, JobApplicationStatus.APPLIED, db_path=db_path,
    )
    return [a for a in rows if _date_in_range(a.applied_date, start, end)]


def _filter_outcomes(
    session_id: str, start: date, end: date, db_path: str | Path,
) -> list[OutcomeRecord]:
    """Outcome records for the session whose created_at falls in range."""
    tracker = OutcomeTracker(db_path)
    rows = tracker.list_by_session(session_id)
    return [r for r in rows if _in_range(_parse_iso(r.created_at), start, end)]


def _load_progressed_applications(
    session_id: str,
    outcomes: list[OutcomeRecord],
    db_path: str | Path,
) -> list[JobApplication]:
    """Hydrate applications referenced by progression-type outcome rows.

    The outcome snapshot columns don't carry the application_id, so we
    re-derive progression by comparing each application's current status
    against the set of outcome event types in the window. An application
    is considered 'progressed' when:
      * it has at least one outcome in-window with a signal_type in
        _PROGRESSED_EVENT_TYPES AND the application belongs to this session.

    Implementation: scan the session's apps, keep those whose current
    status is INTERVIEW or OFFER, if any in-window outcome matches those
    progression events for this session.
    """
    if not any(r.signal_type in _PROGRESSED_EVENT_TYPES for r in outcomes):
        return []
    session_apps = applications.list_by_session(session_id, db_path=db_path)
    progressed_statuses = {
        JobApplicationStatus.INTERVIEW,
        JobApplicationStatus.OFFER,
    }
    return [a for a in session_apps if a.status in progressed_statuses]


def _collect_checklist_items(
    session_id: str,
    start: date,
    end: date,
    db_path: str | Path,
) -> list[dict]:
    """Return checklist items completed in range.

    TODO: no structured `progress_checklist` table exists yet. The only
    storage is `sessions.action_checklist` (opaque JSON) which has no
    per-item completion timestamps. Returning [] until a schema lands.
    """
    return []


def collect_evidence(
    session_id: str,
    *,
    start: date,
    end: date,
    db_path: str | Path,
) -> EvidenceBundle:
    """Collect all progress signals for a session in an inclusive date range.

    Args:
        session_id: Session UUID to scope the query.
        start: First day included (00:00:00 UTC).
        end: Last day included (23:59:59.999999 UTC).
        db_path: SQLite DB path — same store hosting appointments,
            job_applications, and outcomes_records.

    Returns:
        Populated `EvidenceBundle`. All lists default to empty when no
        signals match.
    """
    outcomes = _filter_outcomes(session_id, start, end, db_path)
    return EvidenceBundle(
        session_id=session_id,
        date_range_start=start,
        date_range_end=end,
        checklist_items_completed=_collect_checklist_items(
            session_id, start, end, db_path,
        ),
        appointments_attended=_filter_appointments(
            session_id, AppointmentStatus.ATTENDED, start, end, db_path,
        ),
        appointments_missed=_filter_appointments(
            session_id, AppointmentStatus.MISSED, start, end, db_path,
        ),
        applications_filed=_filter_applied(session_id, start, end, db_path),
        applications_progressed=_load_progressed_applications(
            session_id, outcomes, db_path,
        ),
        outcomes_logged=outcomes,
    )


__all__ = ["EvidenceBundle", "collect_evidence"]
