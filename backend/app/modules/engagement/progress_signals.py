"""Progress event extraction for stall detection (T12.18 helper).

Reads T12.23's EvidenceBundle over a window large enough to cover the
HARD threshold (default 90 days to allow stall inspection without
false-negative truncation), keyed by barrier_link. Auto-advance
outcomes are unconditionally filtered — see stall_detector module
docstring for the rationale.

Extracted out of stall_detector.py to keep that module under the arch
limit on functions-per-file; this file is a single-responsibility
adapter between EvidenceBundle and the barrier-keyed timestamp map the
detector consumes.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.modules.outcomes.types import OutcomeRecord
from app.modules.plan.evidence_collector import (
    EvidenceBundle,
    collect_evidence,
)

_LOOKBACK_DAYS = 90  # plenty of headroom past HARD_DAYS=14
_AUTO_ADVANCE_EVENT_TYPE = "appointment_auto_advance"


def _parse_outcome_ts(record: OutcomeRecord) -> datetime | None:
    """Parse OutcomeRecord.created_at into an aware UTC datetime."""
    raw = record.created_at
    if not raw:
        return None
    s = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _append(
    out: dict[str | None, list[datetime]],
    key: str | None,
    ts: datetime | None,
) -> None:
    """Append ts to out[key] when ts is not None."""
    if ts is None:
        return
    out.setdefault(key, []).append(ts)


def _gather_appointment_events(
    bundle: EvidenceBundle,
    out: dict[str | None, list[datetime]],
) -> None:
    """Record attended appointments keyed by barrier_link."""
    for appt in bundle.appointments_attended:
        _append(out, appt.barrier_link, appt.starts_at)


def _gather_application_events(
    bundle: EvidenceBundle,
    out: dict[str | None, list[datetime]],
) -> None:
    """Record filed + progressed applications as session-wide (None key)."""
    for app_rec in bundle.applications_filed:
        ts = _date_to_datetime(app_rec.applied_date)
        _append(out, None, ts)
    for app_rec in bundle.applications_progressed:
        ts = app_rec.created_at
        _append(out, None, ts)


def _gather_outcome_events(
    bundle: EvidenceBundle,
    out: dict[str | None, list[datetime]],
) -> None:
    """Record worker-driven outcomes as session-wide; filter auto-advance."""
    for rec in bundle.outcomes_logged:
        if rec.signal_type == _AUTO_ADVANCE_EVENT_TYPE:
            continue
        _append(out, None, _parse_outcome_ts(rec))


def _date_to_datetime(d: date | None) -> datetime | None:
    """Lift a date to UTC midnight on that day (None-safe)."""
    if d is None:
        return None
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)


def collect_progress_events(
    session_id: str,
    *,
    db_path: str | Path,
    now: datetime,
) -> dict[str | None, list[datetime]]:
    """Map `barrier_id | None` -> list of progress event timestamps.

    `None` key = session-wide signal (counts toward every barrier).
    Auto-advance outcomes are filtered at all ages (see module docstring).
    """
    end = now.date()
    start = end - timedelta(days=_LOOKBACK_DAYS)
    bundle = collect_evidence(
        session_id, start=start, end=end, db_path=db_path,
    )
    out: dict[str | None, list[datetime]] = {}
    _gather_appointment_events(bundle, out)
    _gather_application_events(bundle, out)
    _gather_outcome_events(bundle, out)
    return out


__all__ = ["collect_progress_events"]
