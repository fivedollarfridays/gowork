"""Per-action classifier matchers for the daily retro (T12.22).

Split from ``daily_progress.py`` to stay under the module function-count
ceiling. Each matcher returns a RetroAction when it recognizes the
action's shape, or None to let the next matcher try. The final fallback
lives in ``daily_progress._classify_one`` so the public module owns the
default UNDONE verdict.
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel

from app.modules.appointments.types import Appointment
from app.modules.plan.evidence_collector import EvidenceBundle


class ActionClassification(str, Enum):
    """Per-action retro verdict."""

    DONE = "done"
    UNDONE = "undone"
    PARTIAL = "partial"


class RetroAction(BaseModel):
    """One classified expected action in the retro output."""

    action_id: str
    title: str
    classification: ActionClassification
    evidence_note: str | None = None


_APPLICATIONS_N_RE = re.compile(r"(\d+)\s+applications?", re.IGNORECASE)


def _title_text(action: dict) -> str:
    """Lowercase title for keyword matching; falls back to action_id."""
    return str(action.get("title") or action.get("action_id") or "").lower()


def _match_appointment(
    action: dict, candidates: list[Appointment],
) -> Appointment | None:
    """First appointment whose title overlaps (either direction) the action's."""
    needle = _title_text(action)
    for appt in candidates:
        title = (appt.title or "").lower()
        if title and (title in needle or needle in title):
            return appt
    return None


def _make_action(
    action: dict,
    classification: ActionClassification,
    note: str | None = None,
) -> RetroAction:
    """Build a RetroAction from the raw dict + verdict."""
    return RetroAction(
        action_id=str(action["action_id"]),
        title=str(action.get("title", "")),
        classification=classification,
        evidence_note=note,
    )


def classify_appointment(
    action: dict, evidence: EvidenceBundle,
) -> RetroAction | None:
    """Actions whose title mentions an appointment. None if not that shape."""
    if "appointment" not in _title_text(action):
        return None
    attended = _match_appointment(action, evidence.appointments_attended)
    if attended is not None:
        return _make_action(
            action, ActionClassification.DONE, f"attended: {attended.title}",
        )
    missed = _match_appointment(action, evidence.appointments_missed)
    if missed is not None:
        return _make_action(
            action, ActionClassification.UNDONE,
            f"missed appointment: {missed.title}",
        )
    return _make_action(
        action, ActionClassification.UNDONE,
        "no matching appointment evidence",
    )


def classify_applications(
    action: dict, evidence: EvidenceBundle,
) -> RetroAction | None:
    """'Submit N applications' actions. None if not that shape."""
    title = _title_text(action)
    match = _APPLICATIONS_N_RE.search(title)
    if match is None or "application" not in title:
        return None
    target = int(match.group(1))
    filed = len(evidence.applications_filed)
    if filed >= target:
        return _make_action(
            action, ActionClassification.DONE, f"filed {filed} of {target}",
        )
    if filed > 0:
        return _make_action(
            action, ActionClassification.PARTIAL, f"filed {filed} of {target}",
        )
    return _make_action(
        action, ActionClassification.UNDONE, "no applications filed",
    )


def classify_checklist(
    action: dict, evidence: EvidenceBundle,
) -> RetroAction | None:
    """Match against evidence.checklist_items_completed; None if no match."""
    title = _title_text(action)
    for item in evidence.checklist_items_completed:
        item_title = str(item.get("title") or "").lower()
        if item_title and (item_title in title or title in item_title):
            return _make_action(
                action, ActionClassification.DONE,
                f"checklist: {item.get('title', '')}",
            )
    return None


__all__ = [
    "ActionClassification",
    "RetroAction",
    "classify_appointment",
    "classify_applications",
    "classify_checklist",
]
