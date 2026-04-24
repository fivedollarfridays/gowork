"""Plan progress carry-forward helpers (T12.24, S12b).

Ported from ``ops:lib/plan_progress.py`` and adapted to the MontGoWork
plan shape: an :class:`ActionPlan` of phases each containing
:class:`ActionItem` dicts, plus the opaque ``sessions.action_checklist``
JSON column.

The carry-forward contract
--------------------------
When the plan refresher re-runs the pathway/action builder, the worker's
completed checklist items must survive. Without this, every HARD-stall
refresh would reset the worker's progress back to zero — the exact
anti-signal we're trying to avoid.

Action keys are built from ``(phase_id, category, title)`` — the most
stable triple our generators produce today (no per-action UUIDs). Keys
present on the old plan but absent from the new plan are dropped; keys
introduced by the new plan start life as ``completed=False``.

Public API
----------
- :func:`load_existing_progress` — read plan + checklist for a session
- :func:`_extract_progress` — normalize plan/checklist into the
  ``{"checklist": {key: state}}`` progress dict
- :func:`merge_existing_progress` — reconcile new plan with old progress
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

_ACTION_SEPARATOR = "|"


def _action_key(phase_id: str, action: dict[str, Any]) -> str:
    """Compose the stable carry-forward key for an action in a phase."""
    category = str(action.get("category", ""))
    title = str(action.get("title", ""))
    return f"{phase_id}{_ACTION_SEPARATOR}{category}{_ACTION_SEPARATOR}{title}"


def _iter_plan_keys(plan: dict) -> list[str]:
    """Yield every (phase_id, category, title) action key in a plan dict."""
    keys: list[str] = []
    for phase in plan.get("phases", []) or []:
        phase_id = str(phase.get("phase_id", ""))
        for action in phase.get("actions", []) or []:
            if isinstance(action, dict):
                keys.append(_action_key(phase_id, action))
    return keys


def _default_state() -> dict[str, Any]:
    """Shape of a fresh (uncompleted) checklist entry."""
    return {"completed": False, "completed_at": None, "notes": None}


def _extract_progress(
    plan: dict, *, action_checklist: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize a stored plan + checklist JSON into a progress dict.

    Only returns checklist state for action keys that *exist in the plan*.
    Keys in ``action_checklist`` that reference removed actions are dropped.
    """
    checklist_src = action_checklist or {}
    plan_keys = set(_iter_plan_keys(plan))
    checklist: dict[str, Any] = {}
    for key in plan_keys:
        if key in checklist_src:
            checklist[key] = dict(checklist_src[key])
    return {"checklist": checklist}


def _parse_json_col(raw: str | None) -> dict:
    """Parse a JSON string; return empty dict on any failure."""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def load_existing_progress(
    session_id: str, *, db_path: str | Path,
) -> dict[str, Any]:
    """Read ``sessions.plan`` + ``sessions.action_checklist`` for a session.

    Returns the normalized progress dict. Sessions with no plan yet
    return an empty ``{"checklist": {}}``.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT plan, action_checklist FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"checklist": {}}
    plan = _parse_json_col(row[0])
    checklist = _parse_json_col(row[1])
    if not plan:
        return {"checklist": {}}
    return _extract_progress(plan, action_checklist=checklist)


def merge_existing_progress(
    new_plan: dict, progress: dict[str, Any],
) -> dict[str, Any]:
    """Build the new checklist dict that carries forward worker state.

    For each action in ``new_plan``:
      - if the action key exists in ``progress["checklist"]``, copy the
        stored state (``completed``, ``completed_at``, ``notes``)
      - otherwise, seed with a fresh ``_default_state()`` entry

    Returns the new ``action_checklist`` JSON shape ready for storage.
    """
    old_checklist = progress.get("checklist", {}) or {}
    new_checklist: dict[str, Any] = {}
    for key in _iter_plan_keys(new_plan):
        if key in old_checklist:
            new_checklist[key] = dict(old_checklist[key])
        else:
            new_checklist[key] = _default_state()
    return new_checklist


__all__ = [
    "_extract_progress",
    "load_existing_progress",
    "merge_existing_progress",
]
