"""Weekly review composer (T12.22a) — Sunday-only per-session summary.

Aggregates one worker session's activity across a 7-day window into a
:class:`WeeklyReview` record with three sections — funnel movement,
engagement trend, and barriers cleared — plus a markdown rendering of
the report. The orchestrator (T12.25) invokes this only on Sunday runs
and dispatches the result via the same reminder engine pipeline as the
daily digest, with a distinct subject line.

Scope and k-anonymity
---------------------
**Per-session scope only.** Every public function takes a single
``session_id`` and returns counts for that session. There is no
cross-session aggregation in this module — that is a deliberate
k-anonymity sentinel. Cross-session advisor analytics live in
``app.modules.outcomes.intelligence`` and ``intelligence_queries``,
both of which already enforce a 5-session minimum.

If you find yourself wanting to add a "summarize this week across all
sessions" helper here, **stop** — route that work through the existing
intelligence pipeline so the suppression rule applies uniformly.

Data sources
------------
* ``outcomes_records`` — funnel transitions (``job_application_applied``
  / ``job_application_interview`` / ``job_application_offer``) and
  barrier clears (``barrier.cleared`` + legacy ``barrier_resolved``).
* ``engagement_events`` — ``digest_sent`` plus the three
  ``stall_soft`` / ``stall_medium`` / ``stall_hard`` reminder rows.
* ``sendgrid_events`` — ``open`` rows joined on the session's email
  (the webhook ingest from S12a T12.2a only carries ``email`` and
  ``message_id``, not ``session_id``).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from pathlib import Path

from app.modules.plan import _weekly_queries

__all__ = [
    "BarriersClearedSummary",
    "EngagementTrend",
    "FunnelMovement",
    "WeeklyReview",
    "build_weekly_review",
    "format_summary_report",
]


# -------------------- Result dataclasses --------------------


@dataclass(frozen=True)
class FunnelMovement:
    """Job-application transitions counted within the window."""

    draft_to_applied: int
    applied_to_interview: int
    interview_to_offer: int


@dataclass(frozen=True)
class EngagementTrend:
    """Email engagement signals for the window. ``open_rate`` is None when no sends."""

    digests_sent: int
    digests_opened: int
    open_rate: float | None
    reminders_sent: int


@dataclass(frozen=True)
class BarriersClearedSummary:
    """Barriers cleared in the window — total + per-barrier counts."""

    total: int
    by_barrier: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class WeeklyReview:
    """A single worker's week-in-review."""

    session_id: str
    window_start: date
    window_end: date
    funnel_movement: FunnelMovement
    engagement_trend: EngagementTrend
    barriers_cleared: BarriersClearedSummary
    summary_markdown: str


# -------------------- Public API --------------------


def build_weekly_review(
    session_id: str,
    date_range: tuple[date, date],
    *,
    db_path: str | Path,
) -> WeeklyReview:
    """Compose the per-session weekly review for ``date_range``.

    ``date_range`` is ``(window_start, window_end)`` inclusive on both
    ends — typical use is ``(today - timedelta(days=7), today)``.
    """
    window_start, window_end = date_range
    funnel, engagement, barriers = _collect_window_signals(
        session_id, window_start, window_end, db_path=db_path,
    )
    return _assemble_review(
        session_id, window_start, window_end, funnel, engagement, barriers,
    )


def _collect_window_signals(
    session_id: str,
    window_start: date,
    window_end: date,
    *,
    db_path: str | Path,
) -> tuple["FunnelMovement", "EngagementTrend", "BarriersClearedSummary"]:
    """Open one DB connection, run the three section queries, close it."""
    start_iso = _to_window_start_iso(window_start)
    end_iso = _to_window_end_iso(window_end)
    conn = sqlite3.connect(str(db_path))
    try:
        funnel = _weekly_queries.fetch_funnel_movement(
            conn, session_id, start_iso, end_iso,
        )
        engagement = _weekly_queries.fetch_engagement_trend(
            conn, session_id, start_iso, end_iso,
        )
        barriers = _weekly_queries.fetch_barriers_cleared(
            conn, session_id, start_iso, end_iso,
        )
    finally:
        conn.close()
    return funnel, engagement, barriers


def _assemble_review(
    session_id: str,
    window_start: date,
    window_end: date,
    funnel: FunnelMovement,
    engagement: EngagementTrend,
    barriers: BarriersClearedSummary,
) -> WeeklyReview:
    """Render markdown then build the final WeeklyReview record."""
    skeleton = WeeklyReview(
        session_id=session_id,
        window_start=window_start,
        window_end=window_end,
        funnel_movement=funnel,
        engagement_trend=engagement,
        barriers_cleared=barriers,
        summary_markdown="",
    )
    summary = format_summary_report(skeleton)
    return WeeklyReview(
        session_id=session_id,
        window_start=window_start,
        window_end=window_end,
        funnel_movement=funnel,
        engagement_trend=engagement,
        barriers_cleared=barriers,
        summary_markdown=summary,
    )


def format_summary_report(review: WeeklyReview) -> str:
    """Render the review as markdown. Quiet weeks get a friendly fallback."""
    if _is_empty_review(review):
        return _quiet_week_markdown(review.window_start, review.window_end)
    parts: list[str] = [
        f"# Weekly review — {review.window_start.isoformat()} "
        f"to {review.window_end.isoformat()}",
        "",
        _funnel_section(review.funnel_movement),
        _engagement_section(review.engagement_trend),
        _barriers_section(review.barriers_cleared),
    ]
    return "\n".join(parts).rstrip() + "\n"


# -------------------- Window helpers --------------------


def _to_window_start_iso(d: date) -> str:
    """Inclusive lower bound — start of the day in UTC."""
    return datetime.combine(d, time.min, tzinfo=timezone.utc).isoformat()


def _to_window_end_iso(d: date) -> str:
    """Inclusive upper bound — end of the day in UTC.

    Tests insert with ``created_at = window_end`` (Sunday 02:00 UTC) so
    the comparison must be ``<=`` against ``end-of-day``.
    """
    return datetime.combine(d, time.max, tzinfo=timezone.utc).isoformat()


# -------------------- Markdown helpers --------------------


def _is_empty_review(review: WeeklyReview) -> bool:
    f = review.funnel_movement
    e = review.engagement_trend
    b = review.barriers_cleared
    return (
        f.draft_to_applied == 0
        and f.applied_to_interview == 0
        and f.interview_to_offer == 0
        and e.digests_sent == 0
        and e.digests_opened == 0
        and e.reminders_sent == 0
        and b.total == 0
    )


def _quiet_week_markdown(start: date, end: date) -> str:
    return (
        f"# Weekly review — {start.isoformat()} to {end.isoformat()}\n"
        "\n"
        "It was a quiet week. No new applications, no engagement signals, "
        "and no barriers cleared in this window. Even quiet weeks count — "
        "rest, regroup, and pick one small step for the week ahead.\n"
    )


def _funnel_section(funnel: FunnelMovement) -> str:
    lines = [
        "## Funnel movement",
        f"- Drafts → applied: **{funnel.draft_to_applied}**",
        f"- Applied → interview: **{funnel.applied_to_interview}**",
        f"- Interview → offer: **{funnel.interview_to_offer}**",
        "",
    ]
    return "\n".join(lines)


def _engagement_section(trend: EngagementTrend) -> str:
    if trend.open_rate is None:
        rate = "n/a"
    else:
        rate = f"{trend.open_rate * 100:.0f}%"
    lines = [
        "## Engagement",
        f"- Digests sent: **{trend.digests_sent}**",
        f"- Digests opened: **{trend.digests_opened}** (open rate: {rate})",
        f"- Reminders sent: **{trend.reminders_sent}**",
        "",
    ]
    return "\n".join(lines)


def _barriers_section(barriers: BarriersClearedSummary) -> str:
    if barriers.total == 0:
        return "## Barriers cleared\nNone this week.\n"
    bullets = [
        f"- {name}: **{count}**"
        for name, count in sorted(barriers.by_barrier.items())
    ]
    return (
        "## Barriers cleared\n"
        f"Total: **{barriers.total}**\n"
        + "\n".join(bullets)
        + "\n"
    )


# Re-export the helper module's json schema so tests / external callers
# can introspect the on-disk payload shapes if needed. Pure namespace
# convenience — no behavior.
_JSON_LOADS = json.loads
