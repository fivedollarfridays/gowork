"""SQL spoke for :mod:`app.modules.plan.weekly_review`.

Three pure query helpers — funnel movement, engagement trend, and
barriers cleared — over a half-open ``[start_iso, end_iso]`` window
keyed on the per-row ``created_at`` timestamp. The hub module owns the
window boundary computation and dataclass shape; this spoke is just
SQL + minimal projection so the hub stays under the project's
function-count ceiling.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.plan.weekly_review import (
        BarriersClearedSummary,
        EngagementTrend,
        FunnelMovement,
    )


_FUNNEL_EVENT_COLUMNS = {
    "job_application_applied": "draft_to_applied",
    "job_application_interview": "applied_to_interview",
    "job_application_offer": "interview_to_offer",
}

_REMINDER_CATEGORIES = ("stall_soft", "stall_medium", "stall_hard")
_BARRIER_EVENT_TYPES = ("barrier.cleared", "barrier_resolved")


def fetch_funnel_movement(
    conn: sqlite3.Connection,
    session_id: str,
    start_iso: str,
    end_iso: str,
):
    """Return :class:`FunnelMovement` for the session over the window."""
    from app.modules.plan.weekly_review import FunnelMovement
    rows = conn.execute(
        "SELECT event_type, COUNT(*) FROM outcomes_records "
        "WHERE session_id = ? "
        "AND created_at >= ? AND created_at <= ? "
        "AND event_type IN (?, ?, ?) "
        "GROUP BY event_type",
        (session_id, start_iso, end_iso, *_FUNNEL_EVENT_COLUMNS.keys()),
    ).fetchall()
    counts = {col: 0 for col in _FUNNEL_EVENT_COLUMNS.values()}
    for event_type, count in rows:
        col = _FUNNEL_EVENT_COLUMNS.get(event_type)
        if col is not None:
            counts[col] = count
    return FunnelMovement(
        draft_to_applied=counts["draft_to_applied"],
        applied_to_interview=counts["applied_to_interview"],
        interview_to_offer=counts["interview_to_offer"],
    )


def fetch_engagement_trend(
    conn: sqlite3.Connection,
    session_id: str,
    start_iso: str,
    end_iso: str,
):
    """Return :class:`EngagementTrend` for the session over the window."""
    from app.modules.plan.weekly_review import EngagementTrend
    digests_sent = _count_engagement_category(
        conn, session_id, "digest_sent", start_iso, end_iso,
    )
    reminders_sent = sum(
        _count_engagement_category(conn, session_id, cat, start_iso, end_iso)
        for cat in _REMINDER_CATEGORIES
    )
    digests_opened = _count_opens_for_session(
        conn, session_id, start_iso, end_iso,
    )
    open_rate: float | None
    if digests_sent == 0:
        open_rate = None
    else:
        open_rate = digests_opened / digests_sent
    return EngagementTrend(
        digests_sent=digests_sent,
        digests_opened=digests_opened,
        open_rate=open_rate,
        reminders_sent=reminders_sent,
    )


def fetch_barriers_cleared(
    conn: sqlite3.Connection,
    session_id: str,
    start_iso: str,
    end_iso: str,
):
    """Return :class:`BarriersClearedSummary` for the session over the window."""
    from app.modules.plan.weekly_review import BarriersClearedSummary
    rows = conn.execute(
        "SELECT payload_json FROM outcomes_records "
        "WHERE session_id = ? "
        "AND created_at >= ? AND created_at <= ? "
        "AND event_type IN (?, ?)",
        (session_id, start_iso, end_iso, *_BARRIER_EVENT_TYPES),
    ).fetchall()
    counter: Counter[str] = Counter()
    for (payload_json,) in rows:
        barrier_id = _extract_barrier_id(payload_json)
        if barrier_id is None:
            continue
        counter[barrier_id] += 1
    return BarriersClearedSummary(
        total=sum(counter.values()),
        by_barrier=dict(counter),
    )


# -------------------- Internal helpers --------------------


def _count_engagement_category(
    conn: sqlite3.Connection,
    session_id: str,
    category: str,
    start_iso: str,
    end_iso: str,
) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM engagement_events "
        "WHERE session_id = ? AND category = ? "
        "AND created_at >= ? AND created_at <= ?",
        (session_id, category, start_iso, end_iso),
    ).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def _count_opens_for_session(
    conn: sqlite3.Connection,
    session_id: str,
    start_iso: str,
    end_iso: str,
) -> int:
    """Count sendgrid 'open' events for the email on the session profile.

    The webhook ingest stores ``email`` only (no ``session_id``), so we
    join via ``sessions.profile.email``. Sessions without an email on
    record return zero — same defensive default as the digest pipeline.
    """
    email = _resolve_session_email(conn, session_id)
    if email is None:
        return 0
    row = conn.execute(
        "SELECT COUNT(*) FROM sendgrid_events "
        "WHERE event_type = 'open' AND email = ? "
        "AND created_at >= ? AND created_at <= ?",
        (email, start_iso, end_iso),
    ).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def _resolve_session_email(
    conn: sqlite3.Connection, session_id: str,
) -> str | None:
    row = conn.execute(
        "SELECT profile FROM sessions WHERE id = ?", (session_id,),
    ).fetchone()
    if not row or not row[0]:
        return None
    try:
        profile = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(profile, dict):
        return None
    email = profile.get("email")
    return email.strip() if isinstance(email, str) and email.strip() else None


def _extract_barrier_id(payload_json: str | None) -> str | None:
    if not payload_json:
        return None
    try:
        payload = json.loads(payload_json)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    barrier_id = payload.get("barrier_id")
    return barrier_id if isinstance(barrier_id, str) and barrier_id else None
