"""Window-boundary tests for the weekly review composer (T13.66).

Pins boundary policy at edges ``test_weekly_review.py`` does not cover:
mid-week session, fully-engaged week, no-data graceful empty,
DST spring-forward + fall-back, and exact 7-day inclusion / 8-day exclusion.

Policy pinned: ``date_range`` is closed on both ends at the calendar-date
level (expanded to ``[start_of_day_utc, end_of_day_utc]``). DST-safe by
construction — UTC date bounds neutralize spring/fall transitions.
Composer does NOT truncate by ``sessions.created_at``; earlier events
for a mid-week session simply don't exist (FK to sessions(id)).

All time-sensitive tests use ``_fake_clock.freeze_time`` (T13.5).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from app.core import feature_flags
from app.core.migrations import runner
from tests._fake_clock import freeze_time

_SUNDAY_2026_04_26 = "2026-04-26T02:00:00+00:00"
_FOR_DATE_SUNDAY = date(2026, 4, 26)
_WINDOW_START_SUNDAY = _FOR_DATE_SUNDAY - timedelta(days=7)

# US DST 2026 anchors — composer must treat as ordinary 7-day weeks.
_SUNDAY_DST_SPRING = "2026-03-08T12:00:00+00:00"
_FOR_DATE_DST_SPRING = date(2026, 3, 8)
_WINDOW_START_DST_SPRING = _FOR_DATE_DST_SPRING - timedelta(days=7)
_SUNDAY_DST_FALL = "2026-11-01T12:00:00+00:00"
_FOR_DATE_DST_FALL = date(2026, 11, 1)
_WINDOW_START_DST_FALL = _FOR_DATE_DST_FALL - timedelta(days=7)


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _reset_feature_flags():
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "weekly_boundaries.db")
    runner.apply_pending(path)
    return path


# -------------------- Seed helpers --------------------


def _exec(db_path: str, sql: str, params: tuple) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def _seed_session(
    db_path: str, session_id: str, *,
    email: str | None = "worker@example.com",
    created_at: datetime | None = None,
) -> None:
    """Insert a session row. ``created_at`` pins when the session came
    into existence — used by mid-week tests."""
    profile: dict[str, Any] = {"first_name": "Worker"}
    if email is not None:
        profile["email"] = email
    when = created_at or datetime.now(timezone.utc)
    _exec(
        db_path,
        "INSERT INTO sessions "
        "(id, created_at, barriers, profile, expires_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            session_id, when.isoformat(), json.dumps([]),
            json.dumps(profile),
            (when + timedelta(days=30)).isoformat(),
        ),
    )


def _insert_outcome(
    db_path: str, session_id: str, event_type: str, *,
    payload: dict[str, Any] | None = None, created_at: datetime,
) -> None:
    _exec(
        db_path,
        "INSERT INTO outcomes_records "
        "(session_id, event_type, payload_json, created_at) "
        "VALUES (?, ?, ?, ?)",
        (
            session_id, event_type,
            json.dumps(payload or {}), created_at.isoformat(),
        ),
    )


def _insert_engagement(
    db_path: str, session_id: str, category: str, *, created_at: datetime,
) -> None:
    _exec(
        db_path,
        "INSERT INTO engagement_events "
        "(session_id, category, payload_json, created_at) "
        "VALUES (?, ?, ?, ?)",
        (session_id, category, json.dumps({}), created_at.isoformat()),
    )


def _insert_sendgrid_open(
    db_path: str, email: str, *, created_at: datetime,
) -> None:
    _exec(
        db_path,
        "INSERT INTO sendgrid_events "
        "(event_type, email, message_id, reason, raw_payload_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("open", email, None, None, json.dumps({}), created_at.isoformat()),
    )


def _seed_full_week(
    db_path: str, session_id: str, email: str, anchor: datetime,
) -> None:
    """5 digests + 3 opens + 1 reminder + 3 funnel + 1 barrier-clear."""
    mid = anchor - timedelta(days=4)
    for ev in (
        "job_application_applied",
        "job_application_interview",
        "job_application_offer",
    ):
        _insert_outcome(db_path, session_id, ev, created_at=mid)
    for offset in (1, 2, 3, 4, 5):
        _insert_engagement(
            db_path, session_id, "digest_sent",
            created_at=anchor - timedelta(days=offset),
        )
    for offset in (1, 2, 3):
        _insert_sendgrid_open(
            db_path, email, created_at=anchor - timedelta(days=offset),
        )
    _insert_engagement(
        db_path, session_id, "stall_soft",
        created_at=anchor - timedelta(days=2),
    )
    _insert_outcome(
        db_path, session_id, "barrier.cleared",
        payload={"barrier_id": "dmv"}, created_at=mid,
    )


def _build(session_id: str, window_start: date, window_end: date, db_path: str):
    """Thin wrapper to keep test bodies short."""
    from app.modules.plan.weekly_review import build_weekly_review
    return build_weekly_review(
        session_id, (window_start, window_end), db_path=db_path,
    )


# -------------------- Cycle 1: full + empty windows --------------------


def test_full_window_full_data(db_path: str) -> None:
    """2-week-old session with 5/7 days of engagement → all sections populated."""
    with freeze_time(_SUNDAY_2026_04_26):
        anchor = datetime.now(timezone.utc)
        _seed_session(
            db_path, "sid-full",
            created_at=anchor - timedelta(days=14),
        )
        _seed_full_week(db_path, "sid-full", "worker@example.com", anchor)
        review = _build(
            "sid-full", _WINDOW_START_SUNDAY, _FOR_DATE_SUNDAY, db_path,
        )

    assert review.funnel_movement.draft_to_applied == 1
    assert review.funnel_movement.applied_to_interview == 1
    assert review.funnel_movement.interview_to_offer == 1
    assert review.engagement_trend.digests_sent == 5
    assert review.engagement_trend.digests_opened == 3
    assert review.engagement_trend.open_rate is not None
    assert abs(review.engagement_trend.open_rate - 0.6) < 1e-6
    assert review.engagement_trend.reminders_sent == 1
    assert review.barriers_cleared.total == 1
    assert review.barriers_cleared.by_barrier == {"dmv": 1}
    md_lower = review.summary_markdown.lower()
    assert "quiet week" not in md_lower
    for section in ("funnel", "engagement", "barrier"):
        assert section in md_lower


def test_no_engagement_data_returns_empty_digest_gracefully(
    db_path: str,
) -> None:
    """No rows in 7 days → valid review with zeroed sections, no crash.

    The "Sunday email about nothing" case: compose returns a valid
    :class:`WeeklyReview` — never None, never a KeyError, never missing
    attributes."""
    with freeze_time(_SUNDAY_2026_04_26):
        anchor = datetime.now(timezone.utc)
        _seed_session(
            db_path, "sid-empty", created_at=anchor - timedelta(days=10),
        )
        review = _build(
            "sid-empty", _WINDOW_START_SUNDAY, _FOR_DATE_SUNDAY, db_path,
        )

    assert review is not None
    assert review.session_id == "sid-empty"
    assert review.window_start == _WINDOW_START_SUNDAY
    assert review.window_end == _FOR_DATE_SUNDAY
    assert review.funnel_movement.draft_to_applied == 0
    assert review.funnel_movement.applied_to_interview == 0
    assert review.funnel_movement.interview_to_offer == 0
    assert review.engagement_trend.digests_sent == 0
    assert review.engagement_trend.digests_opened == 0
    assert review.engagement_trend.open_rate is None  # divide-by-zero guard
    assert review.engagement_trend.reminders_sent == 0
    assert review.barriers_cleared.total == 0
    assert review.barriers_cleared.by_barrier == {}
    assert review.summary_markdown
    assert "quiet week" in review.summary_markdown.lower()


# -------------------- Cycle 2: mid-week + window edges --------------------


def test_partial_window_session_created_midweek(db_path: str) -> None:
    """Session created Wed (4 days before Sun review).

    Composer trusts caller's ``date_range`` and does NOT truncate by
    ``sessions.created_at``; earlier events simply don't exist (FK).
    Verify Wed→Sun events count, no crash, no quiet-week fallback."""
    with freeze_time(_SUNDAY_2026_04_26):
        anchor = datetime.now(timezone.utc)
        wed_creation = anchor - timedelta(days=4)
        _seed_session(db_path, "sid-mid", created_at=wed_creation)
        _insert_engagement(
            db_path, "sid-mid", "digest_sent",
            created_at=wed_creation + timedelta(days=1),
        )
        _insert_engagement(
            db_path, "sid-mid", "digest_sent",
            created_at=wed_creation + timedelta(days=2),
        )
        _insert_outcome(
            db_path, "sid-mid", "job_application_applied",
            created_at=wed_creation + timedelta(days=2),
        )
        review = _build(
            "sid-mid", _WINDOW_START_SUNDAY, _FOR_DATE_SUNDAY, db_path,
        )

    # Window endpoints unchanged — composer doesn't shrink them.
    assert review.window_start == _WINDOW_START_SUNDAY
    assert review.window_end == _FOR_DATE_SUNDAY
    assert review.engagement_trend.digests_sent == 2
    assert review.funnel_movement.draft_to_applied == 1
    assert "quiet week" not in review.summary_markdown.lower()


@pytest.mark.parametrize(
    "boundary_factory,label",
    [
        (
            lambda: datetime.combine(
                _WINDOW_START_SUNDAY, datetime.min.time(),
                tzinfo=timezone.utc,
            ),
            "lower-00:00:00",
        ),
        (
            lambda: datetime.combine(
                _FOR_DATE_SUNDAY,
                datetime.max.time().replace(microsecond=0),
                tzinfo=timezone.utc,
            ),
            "upper-23:59:59",
        ),
    ],
)
def test_window_boundary_inclusive(
    db_path: str, boundary_factory, label: str,
) -> None:
    """Events at exact boundary timestamps are INCLUDED on both ends.

    Pins the closed-on-both-ends policy: ``window_start 00:00:00 UTC``
    and ``window_end 23:59:59 UTC`` both qualify."""
    with freeze_time(_SUNDAY_2026_04_26):
        anchor = datetime.now(timezone.utc)
        _seed_session(
            db_path, f"sid-{label}", created_at=anchor - timedelta(days=14),
        )
        _insert_outcome(
            db_path, f"sid-{label}", "job_application_applied",
            created_at=boundary_factory(),
        )
        review = _build(
            f"sid-{label}", _WINDOW_START_SUNDAY, _FOR_DATE_SUNDAY, db_path,
        )
    assert review.funnel_movement.draft_to_applied == 1, (
        f"event at {label} boundary should be counted (inclusive policy)"
    )


def test_event_outside_window_excluded(db_path: str) -> None:
    """Events 1 second BEFORE ``window_start 00:00 UTC`` and 8 days ago
    are EXCLUDED. Pairs with the inclusive-lower test."""
    with freeze_time(_SUNDAY_2026_04_26):
        anchor = datetime.now(timezone.utc)
        _seed_session(
            db_path, "sid-out", created_at=anchor - timedelta(days=14),
        )
        before = datetime.combine(
            _WINDOW_START_SUNDAY - timedelta(days=1),
            datetime.max.time().replace(microsecond=0),
            tzinfo=timezone.utc,
        )
        eight_days_ago = anchor - timedelta(days=8)
        _insert_outcome(
            db_path, "sid-out", "job_application_applied", created_at=before,
        )
        _insert_outcome(
            db_path, "sid-out", "job_application_applied",
            created_at=eight_days_ago,
        )
        _insert_engagement(
            db_path, "sid-out", "digest_sent", created_at=eight_days_ago,
        )
        review = _build(
            "sid-out", _WINDOW_START_SUNDAY, _FOR_DATE_SUNDAY, db_path,
        )
    assert review.funnel_movement.draft_to_applied == 0
    assert review.engagement_trend.digests_sent == 0


# -------------------- Cycle 3: DST transitions --------------------


def _seed_dst_window(
    db_path: str, session_id: str, window_start: date,
    seed_anchor: datetime,
) -> None:
    """Insert one digest_sent event at noon UTC on each of the 8 calendar
    days in the inclusive window."""
    _seed_session(db_path, session_id, created_at=seed_anchor)
    for offset in range(8):  # inclusive 7-day range = 8 calendar days
        day = window_start + timedelta(days=offset)
        ts = datetime.combine(
            day, datetime.min.time().replace(hour=12), tzinfo=timezone.utc,
        )
        _insert_engagement(db_path, session_id, "digest_sent", created_at=ts)


def test_dst_spring_forward_seven_days(db_path: str) -> None:
    """Window containing 2026-03-08 (US spring forward) counts 7 calendar
    days, not 7*24 hours. A buggy ``now - timedelta(hours=168)`` would
    drop an event in the missing 02:00→03:00 slot. UTC date bounds are
    DST-safe; pin so a future "switch to local time" refactor breaks loud."""
    with freeze_time(_SUNDAY_DST_SPRING):
        _seed_dst_window(
            db_path, "sid-spring", _WINDOW_START_DST_SPRING,
            datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc),
        )
        review = _build(
            "sid-spring", _WINDOW_START_DST_SPRING,
            _FOR_DATE_DST_SPRING, db_path,
        )
    assert review.engagement_trend.digests_sent == 8


def test_dst_fall_back_seven_days(db_path: str) -> None:
    """Window containing 2026-11-01 (US fall back) counts 7 calendar
    days, not 7*24+1 hours. Symmetric to spring-forward."""
    with freeze_time(_SUNDAY_DST_FALL):
        _seed_dst_window(
            db_path, "sid-fall", _WINDOW_START_DST_FALL,
            datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc),
        )
        review = _build(
            "sid-fall", _WINDOW_START_DST_FALL, _FOR_DATE_DST_FALL, db_path,
        )
    assert review.engagement_trend.digests_sent == 8


def test_dst_spring_forward_includes_transition_day(db_path: str) -> None:
    """Every hour of the transition day 2026-03-08 is counted.

    Belt-and-suspenders against a future "local-time bounds" refactor:
    seed 24 events (one per UTC hour) on the spring-forward day and
    assert all 24 count. A local-time-anchored window would silently
    drop the missing 02:00 hour."""
    with freeze_time(_SUNDAY_DST_SPRING):
        _seed_session(
            db_path, "sid-spring-day",
            created_at=datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc),
        )
        for hour in range(24):
            ts = datetime(2026, 3, 8, hour, 0, tzinfo=timezone.utc)
            _insert_engagement(
                db_path, "sid-spring-day", "digest_sent", created_at=ts,
            )
        review = _build(
            "sid-spring-day", _WINDOW_START_DST_SPRING,
            _FOR_DATE_DST_SPRING, db_path,
        )
    assert review.engagement_trend.digests_sent == 24
