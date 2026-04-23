"""Jobs funnel analytics with k-anonymity (T12.12).

Public surface:
    compute_funnel(session_id)              — per-session counts + conversion rates.
    compute_community_funnel(city, ...)     — city-scoped aggregate with k-anonymity.
    build_application_conversion_rates(city) — three-slice payload for /api/intelligence.

K-anonymity
-----------
Community cells containing fewer than `MIN_K_ANONYMITY` (5) distinct
sessions return a `SuppressedCell` instead of counts. The empty-DB case
returns zero counts under the "__all__" key (no PII risk at zero).

Demo session guard
------------------
S12b T12.34 will add a `sessions.demo` column. Until then, the guard
runs a PRAGMA to detect the column and, when present, excludes rows
with `demo=1`. When absent the guard is a no-op — S12b activates it
automatically on migration. Session IDs starting with the literal
`demo-` prefix are *not* filtered; the column is the single source of
truth.

City scope
----------
Sessions are scoped to a city via `outcomes_records.payload_json.city`
(the canonical multi-city tag since S2). A session must have at least
one outcomes_records row matching the target city to be included.
Sessions with no outcomes_records are excluded from city-scoped
aggregates.

Industry segmentation
---------------------
`job_applications` has no industry column and no project-wide industry
classifier exists yet, so `segment_by="industry"` returns a single
`{"__unsupported__": SuppressedCell}` entry documenting the TODO.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from app.modules.common.temporal_types import JobApplicationStatus
from app.modules.jobs import funnel_queries
from app.modules.jobs.funnel_segmentation import (
    FairChanceLookup,
    segments_by_cleared_barriers,
    segments_by_fair_chance,
)

MIN_K_ANONYMITY = 5

SegmentBy = Literal["cleared_barriers", "fair_chance_employer", "industry"]


class FunnelCounts(BaseModel):
    draft: int = 0
    applied: int = 0
    interview: int = 0
    offer: int = 0
    rejected: int = 0
    withdrawn: int = 0


class FunnelResult(BaseModel):
    counts: FunnelCounts
    draft_to_applied_rate: float | None
    applied_to_interview_rate: float | None
    interview_to_offer_rate: float | None


class SuppressedCell(BaseModel):
    count: None = None
    suppressed: Literal[True] = True
    reason: Literal["k_anonymity_min_5"] = "k_anonymity_min_5"


# -------------------- Public API --------------------


def compute_funnel(session_id: str, *, db_path: str | Path) -> FunnelResult:
    """Per-session counts + conversion rates across all of the session's apps."""
    rows = funnel_queries.fetch_status_rows_for_session(session_id, db_path)
    counts = _tally_counts([status for (_app_id, status) in rows])
    return _build_funnel_result(counts)


def compute_community_funnel(
    city: str,
    *,
    segment_by: SegmentBy | None = None,
    db_path: str | Path,
    fair_chance_lookup: FairChanceLookup | None = None,
) -> dict[str, FunnelResult | SuppressedCell]:
    """City-scoped aggregate funnel with optional segmentation + k-anonymity."""
    if segment_by == "industry":
        return {"__unsupported__": SuppressedCell()}

    session_ids = funnel_queries.city_scoped_session_ids(city, db_path)
    rows = funnel_queries.fetch_status_rows_for_sessions(session_ids, db_path)
    if segment_by is None:
        return _aggregate_single_group(session_ids, rows)
    return _aggregate_segmented(
        session_ids, rows, segment_by, db_path, fair_chance_lookup,
    )


def build_application_conversion_rates(
    city: str, *, db_path: str | Path,
) -> dict:
    """Three-slice payload consumed by `/api/intelligence/barriers`."""
    return {
        "city_scoped": compute_community_funnel(city, db_path=db_path),
        "by_cleared_barriers": compute_community_funnel(
            city, segment_by="cleared_barriers", db_path=db_path,
        ),
        "by_fair_chance": compute_community_funnel(
            city, segment_by="fair_chance_employer", db_path=db_path,
        ),
    }


# -------------------- Group aggregation --------------------


def _aggregate_single_group(
    session_ids: set[str],
    rows: list[tuple[str, str]],
) -> dict[str, FunnelResult | SuppressedCell]:
    """Single '__all__' cell. Empty DB → zero counts (no PII risk)."""
    if not session_ids:
        return {"__all__": _build_funnel_result(FunnelCounts())}
    if len(session_ids) < MIN_K_ANONYMITY:
        return {"__all__": SuppressedCell()}
    counts = _tally_counts([status for (_sid, status) in rows])
    return {"__all__": _build_funnel_result(counts)}


def _aggregate_segmented(
    session_ids: set[str],
    rows: list[tuple[str, str]],
    segment_by: SegmentBy,
    db_path: str | Path,
    fair_chance_lookup: FairChanceLookup | None,
) -> dict[str, FunnelResult | SuppressedCell]:
    """Split sessions into named groups; apply k-anonymity per group."""
    session_to_segments = _resolve_segments(
        segment_by, session_ids, db_path, fair_chance_lookup,
    )
    groups, group_rows = _bucket_rows_by_segment(session_to_segments, rows)
    return _finalize_segmented(groups, group_rows)


def _bucket_rows_by_segment(
    session_to_segments: dict[str, list[str]],
    rows: list[tuple[str, str]],
) -> tuple[dict[str, set[str]], dict[str, list[str]]]:
    groups: dict[str, set[str]] = {}
    group_rows: dict[str, list[str]] = {}
    for sid, segs in session_to_segments.items():
        for seg in segs:
            groups.setdefault(seg, set()).add(sid)
            group_rows.setdefault(seg, [])
    for sid, status in rows:
        for seg in session_to_segments.get(sid, []):
            group_rows[seg].append(status)
    return groups, group_rows


def _finalize_segmented(
    groups: dict[str, set[str]],
    group_rows: dict[str, list[str]],
) -> dict[str, FunnelResult | SuppressedCell]:
    result: dict[str, FunnelResult | SuppressedCell] = {}
    for seg, sids in groups.items():
        if len(sids) < MIN_K_ANONYMITY:
            result[seg] = SuppressedCell()
        else:
            result[seg] = _build_funnel_result(_tally_counts(group_rows[seg]))
    return result


def _resolve_segments(
    segment_by: SegmentBy,
    session_ids: set[str],
    db_path: str | Path,
    fair_chance_lookup: FairChanceLookup | None,
) -> dict[str, list[str]]:
    if segment_by == "cleared_barriers":
        return segments_by_cleared_barriers(session_ids, db_path)
    if segment_by == "fair_chance_employer":
        return segments_by_fair_chance(session_ids, db_path, fair_chance_lookup)
    return {}


# -------------------- Counting + rate math --------------------


_STATUS_TO_FIELD = {
    JobApplicationStatus.DRAFT.value: "draft",
    JobApplicationStatus.APPLIED.value: "applied",
    JobApplicationStatus.INTERVIEW.value: "interview",
    JobApplicationStatus.OFFER.value: "offer",
    JobApplicationStatus.REJECTED.value: "rejected",
    JobApplicationStatus.WITHDRAWN.value: "withdrawn",
}


def _tally_counts(statuses: list[str]) -> FunnelCounts:
    c = FunnelCounts()
    for s in statuses:
        field = _STATUS_TO_FIELD.get(s)
        if field is not None:
            setattr(c, field, getattr(c, field) + 1)
    return c


def _build_funnel_result(counts: FunnelCounts) -> FunnelResult:
    """Compute conversion rates; None when the denominator is 0."""
    total = (counts.draft + counts.applied + counts.interview
             + counts.offer + counts.rejected + counts.withdrawn)
    past_draft = total - counts.draft
    past_applied = counts.interview + counts.offer
    interview_plus = counts.interview + counts.offer

    return FunnelResult(
        counts=counts,
        draft_to_applied_rate=_safe_rate(past_draft, total),
        applied_to_interview_rate=_safe_rate(past_applied, past_draft),
        interview_to_offer_rate=_safe_rate(counts.offer, interview_plus),
    )


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


__all__ = [
    "MIN_K_ANONYMITY",
    "FunnelCounts",
    "FunnelResult",
    "SuppressedCell",
    "build_application_conversion_rates",
    "compute_community_funnel",
    "compute_funnel",
]
