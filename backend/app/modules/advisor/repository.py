"""City-scoped repository for the advisor inbox (T12.31).

The non-negotiable contract from ``docs/security/advisor-auth.md``
section 10 (C2): every query threads ``city = advisor.city`` **at the
repository layer**. Route handlers never apply the filter in
post-processing; they call into these functions with a ``city``
argument and trust the SQL to do the right thing.

Schema gap
----------
``sessions`` has no ``city`` column in the current migration chain.
City is inferred from ``outcomes_records.payload_json.city`` (see
``m002_s12_worker_companion.py`` and the T12.31a runbook). Sessions
without an outcomes record have no resolvable city and are excluded
from advisor views — the stall detector may report a stall, but with
no city tag the row is out-of-scope for the inbox.

Demo exclusion
--------------
``sessions.demo = TRUE`` rows are excluded here, not at the route
layer. Per T12.34, the column is the single source of truth.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.modules.engagement._batch_stalls import batch_compute_stalls
from app.modules.engagement.stall_detector import (
    StalledSession,
    compute_stall_for_session,
)

__all__ = [
    "AdvisorSessionDetail",
    "AdvisorStalledSession",
    "get_session_detail_for_city",
    "list_stalled_sessions_for_city",
]

_STALL_RANK = {"hard": 3, "medium": 2, "soft": 1, "none": 0}


@dataclass(frozen=True)
class AdvisorStalledSession:
    """Row in the advisor inbox list — one stalled session."""

    session_id: str
    city: str
    stall_level: str
    days_stalled: int


@dataclass(frozen=True)
class AdvisorSessionDetail:
    """Drill-through detail for one session."""

    session_id: str
    city: str
    stall_level: str
    days_stalled: int


def _city_scoped_session_ids(
    db_path: str | Path, city: str,
) -> list[str]:
    """Return non-demo session IDs whose resolved city matches.

    The JSON-path extraction on ``outcomes_records.payload_json.city``
    mirrors the pattern in :mod:`app.modules.outcomes.tracker_sql` and
    :mod:`app.modules.jobs.funnel_queries`. Sessions with multiple
    outcomes rows (typical) collapse via ``DISTINCT``.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT DISTINCT s.id FROM sessions s "
            "INNER JOIN outcomes_records o ON o.session_id = s.id "
            "WHERE json_extract(o.payload_json, '$.city') = ? "
            "AND (s.demo IS NULL OR s.demo = 0)",
            (city,),
        ).fetchall()
    finally:
        conn.close()
    return [sid for (sid,) in rows]


def _resolve_session_city(
    db_path: str | Path, session_id: str,
) -> str | None:
    """Return the single city claim on a session, or None when unresolvable.

    When multiple outcomes rows tag the session with different cities
    (should not happen in practice), the most recent wins.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT json_extract(payload_json, '$.city') "
            "FROM outcomes_records WHERE session_id = ? "
            "AND json_extract(payload_json, '$.city') IS NOT NULL "
            "ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None or row[0] is None:
        return None
    return str(row[0])


def _session_is_demo(db_path: str | Path, session_id: str) -> bool:
    """Return True when the session row is flagged as demo."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT demo FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return False
    return bool(row[0])


def list_stalled_sessions_for_city(
    db_path: str | Path, city: str, *, limit: int = 50,
) -> list[AdvisorStalledSession]:
    """Return stalled sessions for the given city, sorted by severity.

    Sort order: ``stall_level`` (HARD > MEDIUM > SOFT) then
    ``days_stalled`` DESC so the worst case floats to the top.

    Implementation note (T13.90): the per-session call to
    :func:`compute_stall_for_session` here was an N+1 — each session in
    the city scanned 5 queries. We now route through
    :func:`batch_compute_stalls` which loads all signals in a constant
    handful of queries regardless of cohort size. The semantics match
    the per-session helper — see ``backend/tests/test_batch_stalls.py``
    for the parity assertions.
    """
    ids = _city_scoped_session_ids(db_path, city)
    if not ids:
        return []
    summaries = batch_compute_stalls(ids, db_path=db_path)
    stalled: list[AdvisorStalledSession] = []
    for sid in ids:
        days, level, _stalls = summaries[sid]
        if level.value == "none":
            continue
        stalled.append(
            AdvisorStalledSession(
                session_id=sid,
                city=city,
                stall_level=level.value,
                days_stalled=days,
            ),
        )
    stalled.sort(
        key=lambda s: (_STALL_RANK.get(s.stall_level, 0), s.days_stalled),
        reverse=True,
    )
    return stalled[:limit]


def get_session_detail_for_city(
    db_path: str | Path, session_id: str, city: str,
) -> AdvisorSessionDetail | None:
    """Return detail for ``session_id`` IFF its resolved city matches.

    Returns ``None`` when:

    * the session does not exist,
    * no outcomes row gives it a resolvable city,
    * the session is demo-flagged (out of scope for advisors).

    Returns an :class:`AdvisorSessionDetail` with its own ``city``
    field when the session EXISTS but belongs to a different city —
    the route layer converts that to a 403. This shape is deliberate:
    the repository does not raise HTTP exceptions; the route layer
    owns the policy decision.
    """
    if _session_is_demo(db_path, session_id):
        return None
    resolved = _resolve_session_city(db_path, session_id)
    if resolved is None:
        return None
    ss: StalledSession = compute_stall_for_session(
        session_id, db_path=db_path,
    )
    return AdvisorSessionDetail(
        session_id=session_id,
        city=resolved,
        stall_level=ss.stall_level.value,
        days_stalled=ss.days_stalled,
    )
