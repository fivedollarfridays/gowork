"""Daily progress retro module (T12.22).

Compares a session's expected actions for a target date against actual
evidence from T12.23's :func:`collect_evidence` and persists the result
to ``daily_progress_snapshots``.

Expected-actions contract (Option B)
------------------------------------
The ``ActionPlan`` type produced upstream is phase-based (Week 1-2,
Month 1, ...) and carries no per-day binding. The retro therefore
defines its own contract: **for a given date, "expected actions" =
the appointments scheduled to occur on that date** (regardless of
status — attended, missed, or still scheduled). This keeps the retro
deterministic and sourced from tables that already exist today.

Classifier matchers (appointment / applications count / checklist)
live in ``retro_classifiers``; persistence in ``retro_persistence``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import BaseModel

from app.modules.appointments import scheduler
from app.modules.plan.evidence_collector import EvidenceBundle, collect_evidence
from app.modules.plan.retro_classifiers import (
    ActionClassification,
    RetroAction,
    classify_appointment,
    classify_applications,
    classify_checklist,
)
from app.modules.plan.retro_persistence import fetch_snapshot, upsert_snapshot


class RetroResult(BaseModel):
    """Full retro output for one (session, date)."""

    session_id: str
    for_date: date
    actions: list[RetroAction]
    completion_ratio: float
    summary: str


# -------------------- Classification --------------------


def _classify_one(action: dict, evidence: EvidenceBundle) -> RetroAction:
    """Dispatch to the first matcher that recognizes the action shape."""
    for matcher in (classify_appointment, classify_applications, classify_checklist):
        out = matcher(action, evidence)
        if out is not None:
            return out
    return RetroAction(
        action_id=str(action["action_id"]),
        title=str(action.get("title", "")),
        classification=ActionClassification.UNDONE,
        evidence_note="no matching evidence",
    )


def _derive_done_flags(
    expected_actions: list[dict], evidence: EvidenceBundle,
) -> list[RetroAction]:
    """Core classification: each expected action vs. evidence → RetroAction."""
    return [_classify_one(a, evidence) for a in expected_actions]


# -------------------- Orchestration --------------------


def collect_for_date(
    session_id: str, for_date: date, *, db_path: str | Path,
) -> EvidenceBundle:
    """Thin wrapper around :func:`collect_evidence` with a single-day range."""
    return collect_evidence(
        session_id, start=for_date, end=for_date, db_path=db_path,
    )


def _build_expected_from_appointments(
    session_id: str, for_date: date, *, db_path: str | Path, city: str | None = None,
) -> list[dict]:
    """Expected-actions list: every appointment starting on ``for_date`` (city-local)."""
    from app.modules.common.temporal_types import local_date_in_city
    if city is None:
        from app.core.config import get_settings
        city = get_settings().city
    out: list[dict] = []
    for appt in scheduler.list_by_session(session_id, db_path=db_path):
        if appt.starts_at is None or local_date_in_city(appt.starts_at, city) != for_date:
            continue
        out.append({
            "action_id": f"appointment_{appt.id}",
            "title": f"{appt.title} appointment",
        })
    return out


def _compute_ratio(actions: list[RetroAction]) -> float:
    """done / total, with 0 for empty action lists."""
    if not actions:
        return 0.0
    done = sum(1 for a in actions if a.classification is ActionClassification.DONE)
    return done / len(actions)


def _summarize(actions: list[RetroAction], completion_ratio: float) -> str:
    """One-line human-readable summary of the retro."""
    if not actions:
        return "no expected actions for this date"
    done = sum(1 for a in actions if a.classification is ActionClassification.DONE)
    return f"{done}/{len(actions)} actions complete ({completion_ratio:.0%})"


def run_nightly_retro(
    session_id: str, for_date: date, *, db_path: str | Path,
) -> RetroResult:
    """Compare expected actions for ``for_date`` against evidence; persist."""
    expected = _build_expected_from_appointments(
        session_id, for_date, db_path=db_path,
    )
    evidence = collect_for_date(session_id, for_date, db_path=db_path)
    actions = _derive_done_flags(expected, evidence)
    ratio = _compute_ratio(actions)
    result = RetroResult(
        session_id=session_id,
        for_date=for_date,
        actions=actions,
        completion_ratio=ratio,
        summary=_summarize(actions, ratio),
    )
    upsert_snapshot(
        session_id=session_id,
        for_date=for_date,
        expected_actions=expected,
        evidence=evidence,
        actions=actions,
        db_path=db_path,
    )
    return result


def persist(result: RetroResult, *, db_path: str | Path) -> None:
    """Upsert ``daily_progress_snapshots`` row for (session_id, date)."""
    # For a pre-built RetroResult (e.g. constructed in tests), the source
    # EvidenceBundle is unavailable. Persist a placeholder empty bundle so
    # the JSON column stays well-formed.
    empty = EvidenceBundle(
        session_id=result.session_id,
        date_range_start=result.for_date,
        date_range_end=result.for_date,
    )
    upsert_snapshot(
        session_id=result.session_id,
        for_date=result.for_date,
        expected_actions=[],
        evidence=empty,
        actions=result.actions,
        db_path=db_path,
    )


def load(
    session_id: str, for_date: date, *, db_path: str | Path,
) -> RetroResult | None:
    """Read back a previously-persisted snapshot as a RetroResult."""
    row = fetch_snapshot(
        session_id=session_id, for_date=for_date, db_path=db_path,
    )
    if row is None:
        return None
    actions = [RetroAction.model_validate(a) for a in row["classifications"]]
    ratio = _compute_ratio(actions)
    return RetroResult(
        session_id=session_id,
        for_date=for_date,
        actions=actions,
        completion_ratio=ratio,
        summary=_summarize(actions, ratio),
    )


__all__ = [
    "ActionClassification",
    "RetroAction",
    "RetroResult",
    "collect_for_date",
    "load",
    "persist",
    "run_nightly_retro",
]
