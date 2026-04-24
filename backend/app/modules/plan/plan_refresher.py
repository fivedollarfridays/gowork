"""Plan refresher — re-runs pathway + action plan on stall/breakthrough (T12.24).

Triggers
--------
Called nightly from the orchestrator (T12.25) once per active session. It
refreshes the worker's plan when one of:

1. ``stall_level=HARD`` — the worker has been stuck so long that the
   current plan has failed and a new sequence is warranted (T12.18).
2. Breakthrough — an outcomes_records ``barrier_resolved`` row landed in
   the last 24h; the plan should pick up the newly unlocked options.
3. An explicit ``trigger_reason`` argument (manual refreshes, tests).

When no trigger fires the refresher is a strict no-op.

Carry-forward
-------------
Completed checklist items survive the refresh. We port
``load_existing_progress`` / ``_extract_progress`` / ``merge_existing_progress``
from ``ops:lib/plan_progress.py``, adapted to the MontGoWork plan shape
(see ``plan_progress.py``).

Archive + dual-write
--------------------
The old plan is archived to ``plan_history`` (S12a m002) with
``refresh_reason`` and ``triggering_event``. It is *also* copied to
``sessions.previous_plan`` to mirror the legacy column.

Deprecation note (S13): ``sessions.previous_plan`` is duplicated by the
``plan_history`` table. A future sprint will drop the column; until
then we dual-write so in-flight consumers keep working.

Cap enforcement
---------------
``plan_history`` is capped at 20 rows per session — the m002 migration
inline comment promised application-level enforcement; this module is
where it lives.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from app.modules.benefits.types import BenefitsProfile
from app.modules.outcomes.intelligence import compute_calibrated_barriers
from app.modules.pathway.engine import generate_pathways
from app.modules.plan._plan_refresher_db import (
    archive_plan,
    detect_breakthrough,
    detect_stall_hard,
    load_session_row,
    write_new_plan,
)
from app.modules.plan.plan_progress import (
    _extract_progress,
    merge_existing_progress,
)

# Expose compute_stall_for_session at module level so tests can patch
# ``plan_refresher.compute_stall_for_session`` directly without reaching
# into the detector module.
from app.modules.engagement.stall_detector import (  # noqa: E402
    compute_stall_for_session,
)


class RefreshResult(BaseModel):
    """Outcome of a refresh_plan invocation."""

    refreshed: bool
    trigger_reason: str | None = None
    triggering_event: str | None = None


def load_calibrated_weeks(db_path: str | Path) -> dict[str, int]:
    """Return calibrated_weeks from outcomes (sync, sqlite-native).

    The async route-level accessor lives in ``routes/_intelligence_helpers``
    and consumes an ``AsyncSession``. For the nightly orchestrator we need
    a sync read that talks directly to SQLite.
    """
    import json
    import sqlite3

    rows: list[dict] = []
    conn = sqlite3.connect(str(db_path))
    try:
        raw = conn.execute(
            "SELECT s.barriers, vf.outcomes, vf.plan_accuracy "
            "FROM visit_feedback vf JOIN sessions s ON s.id = vf.session_id"
        ).fetchall()
    finally:
        conn.close()
    for barriers_str, outcomes_str, plan_accuracy in raw:
        try:
            barriers = json.loads(barriers_str) if barriers_str else []
            resolved = set(json.loads(outcomes_str) if outcomes_str else [])
        except (json.JSONDecodeError, TypeError):
            continue
        for bid in barriers:
            if not isinstance(bid, str):
                continue
            rows.append({
                "barrier_id": bid,
                "resolved": bid in resolved,
                "weeks_to_resolve": None,
                "plan_accuracy": plan_accuracy,
            })
    return compute_calibrated_barriers(rows).to_weeks_dict()


def _detect_trigger(
    session_id: str, *, db_path: str | Path, now: datetime,
) -> tuple[str | None, str | None]:
    """Auto-detect a refresh trigger (stall + breakthrough). Stall wins if both."""
    stall_event = detect_stall_hard(
        session_id, db_path=db_path, now=now,
        compute_fn=compute_stall_for_session,
    )
    if stall_event is not None:
        return "stall_hard", stall_event
    breakthrough_event = detect_breakthrough(
        session_id, db_path=db_path, now=now,
    )
    if breakthrough_event is not None:
        return "breakthrough", breakthrough_event
    return None, None


def _build_plan_for_session(
    session_row: dict, calibrated_weeks: dict[str, int], today: datetime,
) -> dict:
    """Re-run the pathway engine and emit a plan dict for storage.

    The pathway result is dumped as the new plan body. The merge
    helpers tolerate non-``phases``-shaped plans by carrying nothing
    forward (worker simply starts fresh on those keys), so this is
    safe even though the pathway shape differs from the legacy
    ActionPlan shape.
    """
    barriers = session_row["barriers"]
    try:
        profile = BenefitsProfile(**(session_row["benefits_profile"] or {}))
    except (ValueError, TypeError):
        profile = BenefitsProfile()
    result = generate_pathways(
        barrier_ids=list(barriers),
        benefits_profile=profile,
        current_wage=0.0,
        calibrated_weeks=calibrated_weeks or None,
    )
    payload = result.model_dump()
    payload["assessment_date"] = today.date().isoformat()
    return payload


def _perform_refresh(
    session_id: str,
    session_row: dict,
    *,
    db_path: str | Path,
    reason: str,
    event: str | None,
    now: datetime,
) -> None:
    """Regenerate the plan, archive the old one, and persist carry-forward."""
    old_plan = session_row["plan"] or {}
    calibrated_weeks = load_calibrated_weeks(db_path)
    new_plan = _build_plan_for_session(session_row, calibrated_weeks, now)
    progress = _extract_progress(
        old_plan, action_checklist=session_row["action_checklist"],
    )
    new_checklist = merge_existing_progress(new_plan, progress)
    archive_plan(
        session_id, old_plan, db_path=db_path,
        archived_at=now, refresh_reason=reason, triggering_event=event,
    )
    write_new_plan(
        session_id, db_path=db_path,
        old_plan=old_plan, new_plan=new_plan, new_checklist=new_checklist,
    )


def refresh_plan(
    session_id: str,
    *,
    db_path: str | Path,
    trigger_reason: str | None = None,
    triggering_event: str | None = None,
    now: datetime | None = None,
) -> RefreshResult:
    """Refresh the plan for ``session_id`` if a trigger fires.

    Returns a :class:`RefreshResult` describing whether the refresh
    happened and which trigger fired. When ``trigger_reason`` is passed
    explicitly, auto-detection is bypassed (used for manual refreshes
    and tests).
    """
    resolved_now = now or datetime.now(timezone.utc)
    session_row = load_session_row(session_id, db_path)
    if session_row is None:
        return RefreshResult(refreshed=False)

    reason, event = trigger_reason, triggering_event
    if reason is None:
        reason, event = _detect_trigger(
            session_id, db_path=db_path, now=resolved_now,
        )
    if reason is None:
        return RefreshResult(refreshed=False)

    _perform_refresh(
        session_id, session_row, db_path=db_path,
        reason=reason, event=event, now=resolved_now,
    )
    return RefreshResult(
        refreshed=True, trigger_reason=reason, triggering_event=event,
    )


__all__ = [
    "RefreshResult",
    "load_calibrated_weeks",
    "refresh_plan",
]
