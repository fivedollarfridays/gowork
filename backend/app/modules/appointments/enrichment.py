"""Appointment enrichment + stage advance (T12.7a).

Ported from ``ops:lib/appointment_merge.py`` and wired into the S12a
in-process event bus (``app.core.events``). The scheduler emits
``appointment.attended`` / ``appointment.missed``; this module subscribes
and proposes stage advances. When an advance reaches a terminal stage we
emit ``barrier.cleared(session_id, barrier_id)`` for the intelligence
engine's calibration loop.

Design notes
------------
* ``auto_advance_stage`` is **pure** — it returns a ``StageAdvance`` or
  ``None`` and never mutates the input appointment. Callers (the event
  handler or a future worker) decide whether to persist the advance.
* City-awareness: the stage map is keyed by ``(city_slug, barrier_link)``.
  AL (Montgomery) uses the *expunction* pathway labels; TX (Fort Worth)
  uses *nondisclosure*. Unknown combinations yield ``None``.
* Current stage is encoded as ``"stage:<name>"`` inside the appointment's
  ``notes`` field — the lightweight contract S12a ships before a dedicated
  stage column lands. Absent/unparseable notes fall back to the flow's
  first stage.
* The listener registration is idempotent across lifespan restarts via a
  module-level sentinel (same pattern as ``outcomes_listener``).
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from app.core import events
from app.core.config import get_settings
from app.modules.appointments import persistence
from app.modules.appointments.types import Appointment

logger = logging.getLogger(__name__)

TERMINAL_STAGES: frozenset[str] = frozenset({"cleared", "recerted", "completed"})

# City-aware stage flow. Keys are (city_slug, barrier_link); values are
# the ordered stage pipeline. AL = expunction pathway; TX = nondisclosure.
_STAGE_FLOW: dict[tuple[str, str], list[str]] = {
    ("montgomery", "criminal"): ["filed", "heard", "granted", "cleared"],
    ("fort-worth", "criminal"): ["petitioned", "heard", "ordered", "cleared"],
    ("montgomery", "benefits"): ["enrolled", "recerted"],
    ("fort-worth", "benefits"): ["enrolled", "recerted"],
    ("montgomery", "employment"): ["applied", "interview", "offer", "completed"],
    ("fort-worth", "employment"): ["applied", "interview", "offer", "completed"],
}

# Fields considered when computing diffs / merges. We deliberately skip
# id / created_at / session_id (identity) and status (lifecycle owned by
# the scheduler).
_ENRICHABLE_FIELDS: tuple[str, ...] = (
    "title",
    "starts_at",
    "ends_at",
    "location_name",
    "location_address",
    "barrier_link",
    "notes",
)

_STAGE_NOTE_PREFIX = "stage:"


@dataclass(frozen=True)
class StageAdvance:
    """Proposed stage change. Never mutates the source appointment."""

    from_stage: str
    to_stage: str
    is_terminal: bool


def _parse_current_stage(appointment: Appointment) -> str | None:
    """Extract the 'stage:<name>' token from notes, if present."""
    notes = (appointment.notes or "").strip()
    if not notes:
        return None
    for token in notes.split():
        if token.startswith(_STAGE_NOTE_PREFIX):
            return token[len(_STAGE_NOTE_PREFIX):] or None
    return None


def auto_advance_stage(
    appointment: Appointment, *, city: str | None = None,
) -> StageAdvance | None:
    """Propose the next stage for an attended appointment.

    Returns ``None`` when the appointment has no barrier mapping or is
    already at the terminal stage. Never mutates ``appointment``.
    """
    barrier = appointment.barrier_link
    if barrier is None:
        return None
    city_slug = city or get_settings().city
    flow = _STAGE_FLOW.get((city_slug, barrier))
    if not flow:
        return None

    current = _parse_current_stage(appointment) or flow[0]
    if current not in flow:
        return None
    idx = flow.index(current)
    if idx >= len(flow) - 1:
        return None  # Already terminal — nothing to advance to.
    next_stage = flow[idx + 1]
    return StageAdvance(
        from_stage=current,
        to_stage=next_stage,
        is_terminal=next_stage in TERMINAL_STAGES,
    )


def merge_appointment(existing: Appointment, new: Appointment) -> Appointment:
    """Field-level enrichment: fill None/empty fields in ``existing`` from ``new``.

    Never overwrites a non-null existing value. Returns a new Appointment;
    both inputs are left untouched.
    """
    updates: dict[str, object] = {}
    for field in _ENRICHABLE_FIELDS:
        existing_val = getattr(existing, field)
        new_val = getattr(new, field)
        if _is_empty(existing_val) and not _is_empty(new_val):
            updates[field] = new_val
    return existing.model_copy(update=updates) if updates else existing


def _is_empty(value: object) -> bool:
    """None and empty/whitespace strings count as absent."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def enrichment_changed(
    existing: Appointment, new: Appointment,
) -> dict[str, tuple]:
    """Return ``{field: (old, new)}`` for every enrichable field that differs."""
    diffs: dict[str, tuple] = {}
    for field in _ENRICHABLE_FIELDS:
        old_val = getattr(existing, field)
        new_val = getattr(new, field)
        if old_val != new_val:
            diffs[field] = (old_val, new_val)
    return diffs


def build_pipeline_summary(
    session_id: str, *, db_path: str | Path,
) -> dict[tuple[str, str], int]:
    """Aggregate per-session stage progress as ``{(barrier, stage): count}``."""
    rows = persistence.select_by_session(session_id, db_path=db_path)
    counter: Counter[tuple[str, str]] = Counter()
    for appt in rows:
        if appt.barrier_link is None:
            continue
        stage = _parse_current_stage(appt)
        if stage is None:
            continue
        counter[(appt.barrier_link, stage)] += 1
    return dict(counter)


# -------------------- Event-bus wiring --------------------


_REGISTRATION_SENTINEL: set[str] = set()

# Events we subscribe to for barrier.cleared emission.
_ATTENDED_EVENT = "appointment.attended"
_JOB_OFFER_EVENT = "job_application.offer"


def _handle_attended(payload: dict) -> None:
    """Compute stage advance for an attended appointment; emit barrier.cleared."""
    try:
        appointment = Appointment.model_validate(payload)
    except Exception:  # noqa: BLE001 — malformed payload shouldn't kill the bus
        logger.exception("Malformed appointment.attended payload")
        return
    advance = auto_advance_stage(appointment)
    if advance is None or not advance.is_terminal:
        return
    events.emit(
        "barrier.cleared",
        {
            "session_id": appointment.session_id,
            "barrier_id": appointment.barrier_link,
        },
    )


def _handle_job_offer(payload: dict) -> None:
    """Treat any job_application.offer as clearing the employment barrier."""
    session_id = payload.get("session_id")
    if not session_id:
        return
    events.emit(
        "barrier.cleared",
        {"session_id": session_id, "barrier_id": "employment"},
    )


def register_enrichment_listener(db_path: str | Path) -> None:
    """Subscribe to appointment.attended + job_application.offer. Idempotent.

    The ``db_path`` is accepted for parity with ``register_outcomes_listener``
    and forward-compat with future handlers that need DB access; the
    current handlers are pure over the event payload.
    """
    key = str(db_path)
    if key in _REGISTRATION_SENTINEL:
        return
    events.subscribe(_ATTENDED_EVENT, _handle_attended)
    events.subscribe(_JOB_OFFER_EVENT, _handle_job_offer)
    _REGISTRATION_SENTINEL.add(key)


__all__ = [
    "StageAdvance",
    "TERMINAL_STAGES",
    "auto_advance_stage",
    "build_pipeline_summary",
    "enrichment_changed",
    "merge_appointment",
    "register_enrichment_listener",
]
