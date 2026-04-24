"""Project / work-history ranker for the resume generator (T12.15).

Ported from ``ops:lib/resume_generator.rank_projects``. The ops version
queried the workspace's ``project_metadata`` + ``project_skills``
tables; MontGoWork ranks the worker's own ``work_history`` entries
instead, passed in by the caller as a plain list of dicts.

Scoring is deterministic and keyword-overlap only (the ops build
layered in ``test_count``, ``coverage`` and ``is_portfolio`` — none
of which apply to a real-world worker resume). Tie-break order:

1. Higher keyword hits first.
2. Preserve caller order (stable-sort on a descending key).

Public API
----------
:func:`rank_projects`
    Return a new list; the caller decides whether to truncate.
"""

from __future__ import annotations

from typing import Any

__all__ = ["rank_projects", "score_project"]


# ---------------------------------------------------------------------------
# Scoring primitives.
# ---------------------------------------------------------------------------


def _project_haystack(project: dict[str, Any]) -> str:
    """Concatenate the project's searchable fields into one lowercased blob.

    Accepts both the ops-shape (``description``, ``tech_stack``,
    ``skills``, ``accolades``) and the MontGoWork work-history shape
    (``title``, ``employer``, ``description``) so callers don't have
    to translate.
    """
    parts: list[str] = []
    for key in ("title", "employer", "description", "accolades"):
        value = project.get(key)
        if isinstance(value, str) and value:
            parts.append(value)
    for key in ("tech_stack", "skills"):
        value = project.get(key)
        if isinstance(value, list):
            parts.append(" ".join(str(item) for item in value))
    return " ".join(parts).lower()


def score_project(project: dict[str, Any], keywords: list[str]) -> int:
    """Count how many of ``keywords`` appear in the project's haystack."""
    if not keywords:
        return 0
    haystack = _project_haystack(project)
    return sum(1 for kw in keywords if kw and kw.lower() in haystack)


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------


def rank_projects(
    projects: list[dict[str, Any]],
    keywords: list[str],
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return ``projects`` sorted by keyword-overlap score (desc).

    * Projects with a zero score are kept at the tail — the caller may
      still want to show them when no JD keywords land. Callers that
      want a JD-only cut can filter ``score_project == 0`` beforehand.
    * Sort is stable, so projects with equal scores keep their input
      order.
    * ``limit`` truncates from the head when set.
    """
    if not projects:
        return []
    # Pair each project with (-score, input_index) so Python's stable
    # sort yields descending score with caller order as the tie-break.
    indexed = list(enumerate(projects))
    indexed.sort(key=lambda pair: -score_project(pair[1], keywords))
    ranked = [project for _, project in indexed]
    if limit is not None:
        return ranked[:limit]
    return ranked
