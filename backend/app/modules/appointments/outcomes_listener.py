"""Bridge appointment events → append-only outcomes_records (T12.7).

The scheduler never imports this module — coupling is via the
in-process event bus in `app.core.events`. At startup, `main.py` calls
`register_outcomes_listener(db_path)` which wires handlers for every
appointment event we care about. Each handler constructs an
`OutcomeRecord` (resource_ratings encoding a minimal semantic payload)
and appends it via `OutcomeTracker`.

Event → signal_type mapping:
    appointment.created      → "appointment_created"
    appointment.attended     → "appointment_attended"
    appointment.missed       → "appointment_missed"
    appointment.rescheduled  → "appointment_rescheduled"
"""

from __future__ import annotations

from pathlib import Path

from app.core import events
from app.modules.outcomes.tracker import OutcomeTracker
from app.modules.outcomes.types import OutcomeRecord

_SIGNAL_BY_EVENT: dict[str, str] = {
    "appointment.created": "appointment_created",
    "appointment.attended": "appointment_attended",
    "appointment.missed": "appointment_missed",
    "appointment.rescheduled": "appointment_rescheduled",
}


def _payload_to_record(payload: dict, signal_type: str) -> OutcomeRecord:
    """Build an OutcomeRecord from an appointment event payload."""
    resource_ratings: dict[str, bool] = {}
    # Attended / missed are the primary N+1 signals — mark the barrier_link
    # as "effective" (attended) or "ineffective" (missed) when present.
    barrier_link = payload.get("barrier_link")
    if barrier_link:
        if signal_type == "appointment_attended":
            resource_ratings[barrier_link] = True
        elif signal_type == "appointment_missed":
            resource_ratings[barrier_link] = False
    return OutcomeRecord(
        session_id=payload["session_id"],
        signal_type=signal_type,
        resource_ratings=resource_ratings,
    )


def _make_handler(signal_type: str, db_path: str | Path):
    """Return a handler bound to `signal_type` and the tracker's db_path."""
    tracker = OutcomeTracker(db_path)

    def _handle(payload: dict) -> None:
        record = _payload_to_record(payload, signal_type)
        tracker.record_outcome(record)

    return _handle


def register_outcomes_listener(db_path: str | Path) -> None:
    """Subscribe outcome handlers to every mapped appointment event.

    Idempotent — the bus's `subscribe` is a no-op for duplicates, but
    each call here creates a *new* handler closure, so repeated
    registrations would stack. In practice this is called once at
    startup; callers that need re-registration should first invoke
    `events.clear_all_subscribers()` (e.g. in tests).
    """
    for event_name, signal_type in _SIGNAL_BY_EVENT.items():
        events.subscribe(event_name, _make_handler(signal_type, db_path))


__all__ = ["register_outcomes_listener"]
