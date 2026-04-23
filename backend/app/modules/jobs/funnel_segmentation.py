"""Segmentation strategies for `funnel_analytics` (T12.12).

Each `segments_by_*` helper maps `session_id -> list[segment_key]`.
A session can belong to multiple segment groups (e.g. a session with
two cleared barriers lands in both groups).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from app.modules.jobs import funnel_queries

FairChanceLookup = Callable[[str, str], bool]


def segments_by_cleared_barriers(
    session_ids: set[str], db_path: str | Path,
) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for sid in session_ids:
        cleared = funnel_queries.load_cleared_barriers(sid, db_path)
        out[sid] = list(cleared) if cleared else ["__none__"]
    return out


def segments_by_fair_chance(
    session_ids: set[str],
    db_path: str | Path,
    lookup: FairChanceLookup | None,
) -> dict[str, list[str]]:
    """Tag each session's apps 'true' / 'false' via employer lookup.

    A session goes into 'true' if ANY application targets a fair-chance
    employer; the same session ALSO appears in 'false' when it has
    non-fair-chance applications. Callers may inject a lookup; default
    uses `criminal.fair_chance_index`.
    """
    lookup = lookup or default_fair_chance_lookup
    company_rows = funnel_queries.fetch_company_rows_for_sessions(
        session_ids, db_path,
    )
    out: dict[str, list[str]] = {}
    for sid, company in company_rows:
        flag = "true" if lookup(company or "", "") else "false"
        out.setdefault(sid, [])
        if flag not in out[sid]:
            out[sid].append(flag)
    return out


def default_fair_chance_lookup(company: str, _city: str) -> bool:
    """Project-default lookup: resolve against the criminal fair-chance index."""
    from app.core.config import get_settings
    from app.modules.criminal import fair_chance_index

    city_slug = get_settings().city
    employers = fair_chance_index.get_fair_chance_employers(city_slug)
    target = (company or "").strip().lower()
    if not target:
        return False
    return any(
        isinstance(e, dict) and str(e.get("name", "")).strip().lower() == target
        for e in employers
    )


__all__ = [
    "FairChanceLookup",
    "default_fair_chance_lookup",
    "segments_by_cleared_barriers",
    "segments_by_fair_chance",
]
