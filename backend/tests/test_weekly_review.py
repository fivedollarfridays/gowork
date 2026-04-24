"""Tests for the weekly review composer (T12.22a).

Covers:
- Empty-window "quiet week" build + markdown fallback.
- Funnel movement counts (draft→applied, applied→interview, interview→offer)
  derived from outcomes_records within the 7-day window.
- Engagement trend sourced from engagement_events (digests_sent) and
  sendgrid_events (opens), with open-rate math.
- Barriers cleared: dual event-type handling (barrier.cleared + barrier_resolved).
- Markdown rendering sections and the quiet-week fallback.
- Sunday-only orchestration branch in scripts.nightly_digest — non-Sunday
  skips weekly review; Sunday sends BOTH daily and weekly digests.
- Module docstring documents per-session scope (k-anonymity sentinel).
"""

from __future__ import annotations

import importlib
import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from app.core import feature_flags
from app.core.migrations import runner

_NOW_SUNDAY = datetime(2026, 4, 26, 2, 0, tzinfo=timezone.utc)  # Sunday
_NOW_MONDAY = datetime(2026, 4, 27, 2, 0, tzinfo=timezone.utc)  # Monday
_FOR_DATE_SUNDAY = date(2026, 4, 26)
_WINDOW_START = _FOR_DATE_SUNDAY - timedelta(days=7)


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _reset_feature_flags() -> None:
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "weekly.db")
    runner.apply_pending(path)
    return path


# -------------------- Seed helpers --------------------


def _seed_session(
    db_path: str,
    session_id: str,
    *,
    email: str | None = "worker@example.com",
    city: str | None = "montgomery",
) -> None:
    profile: dict[str, Any] = {"first_name": "Worker"}
    if email is not None:
        profile["email"] = email
    iso = _NOW_SUNDAY.isoformat()
    expires = (_NOW_SUNDAY + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, iso, json.dumps([]), json.dumps(profile), expires),
        )
        if city is not None:
            conn.execute(
                "INSERT INTO outcomes_records "
                "(session_id, event_type, payload_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (session_id, "city_tag", json.dumps({"city": city}), iso),
            )
        conn.commit()
    finally:
        conn.close()


def _insert_outcome(
    db_path: str,
    session_id: str,
    event_type: str,
    *,
    payload: dict[str, Any] | None = None,
    created_at: datetime | None = None,
) -> None:
    ts = (created_at or _NOW_SUNDAY).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, event_type, json.dumps(payload or {}), ts),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_engagement_event(
    db_path: str,
    session_id: str,
    category: str,
    *,
    created_at: datetime | None = None,
) -> None:
    ts = (created_at or _NOW_SUNDAY).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO engagement_events "
            "(session_id, category, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, category, json.dumps({}), ts),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_sendgrid_event(
    db_path: str,
    email: str,
    event_type: str,
    *,
    created_at: datetime | None = None,
) -> None:
    ts = (created_at or _NOW_SUNDAY).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sendgrid_events "
            "(event_type, email, message_id, reason, raw_payload_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (event_type, email, None, None, json.dumps({}), ts),
        )
        conn.commit()
    finally:
        conn.close()


# -------------------- Core builder tests --------------------


def test_build_weekly_review_empty_window(db_path: str) -> None:
    """No signals → all zeros, summary_markdown has the quiet-week fallback."""
    _seed_session(db_path, "sid-1")
    from app.modules.plan.weekly_review import build_weekly_review

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    assert review.session_id == "sid-1"
    assert review.window_start == _WINDOW_START
    assert review.window_end == _FOR_DATE_SUNDAY
    assert review.funnel_movement.draft_to_applied == 0
    assert review.funnel_movement.applied_to_interview == 0
    assert review.funnel_movement.interview_to_offer == 0
    assert review.engagement_trend.digests_sent == 0
    assert review.engagement_trend.digests_opened == 0
    assert review.engagement_trend.open_rate is None
    assert review.engagement_trend.reminders_sent == 0
    assert review.barriers_cleared.total == 0
    assert review.barriers_cleared.by_barrier == {}
    assert "quiet week" in review.summary_markdown.lower()


def test_funnel_movement_counts_transitions(db_path: str) -> None:
    """applied + interview + offer events in window → correct transition counts."""
    _seed_session(db_path, "sid-1")
    mid_window = _NOW_SUNDAY - timedelta(days=3)
    _insert_outcome(db_path, "sid-1", "job_application_applied", created_at=mid_window)
    _insert_outcome(
        db_path, "sid-1", "job_application_interview", created_at=mid_window,
    )
    _insert_outcome(db_path, "sid-1", "job_application_offer", created_at=mid_window)
    from app.modules.plan.weekly_review import build_weekly_review

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    assert review.funnel_movement.draft_to_applied == 1
    assert review.funnel_movement.applied_to_interview == 1
    assert review.funnel_movement.interview_to_offer == 1


def test_engagement_trend_open_rate(db_path: str) -> None:
    """3 digest sends + 2 opens → open_rate ≈ 0.666."""
    _seed_session(db_path, "sid-1", email="worker@example.com")
    mid = _NOW_SUNDAY - timedelta(days=2)
    for _ in range(3):
        _insert_engagement_event(db_path, "sid-1", "digest_sent", created_at=mid)
    _insert_sendgrid_event(db_path, "worker@example.com", "open", created_at=mid)
    _insert_sendgrid_event(db_path, "worker@example.com", "open", created_at=mid)
    from app.modules.plan.weekly_review import build_weekly_review

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    assert review.engagement_trend.digests_sent == 3
    assert review.engagement_trend.digests_opened == 2
    assert review.engagement_trend.open_rate is not None
    assert abs(review.engagement_trend.open_rate - (2 / 3)) < 1e-6


def test_engagement_trend_no_sends_open_rate_none(db_path: str) -> None:
    """Zero digest sends → open_rate is None (divide-by-zero guarded)."""
    _seed_session(db_path, "sid-1")
    from app.modules.plan.weekly_review import build_weekly_review

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    assert review.engagement_trend.digests_sent == 0
    assert review.engagement_trend.open_rate is None


def test_engagement_trend_counts_reminders(db_path: str) -> None:
    """stall_soft/medium/hard engagement events counted as reminders_sent."""
    _seed_session(db_path, "sid-1")
    mid = _NOW_SUNDAY - timedelta(days=3)
    _insert_engagement_event(db_path, "sid-1", "stall_soft", created_at=mid)
    _insert_engagement_event(db_path, "sid-1", "stall_medium", created_at=mid)
    _insert_engagement_event(db_path, "sid-1", "stall_hard", created_at=mid)
    _insert_engagement_event(db_path, "sid-1", "digest_sent", created_at=mid)
    from app.modules.plan.weekly_review import build_weekly_review

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    assert review.engagement_trend.reminders_sent == 3


def test_barriers_cleared_counts_per_barrier(db_path: str) -> None:
    """2 barrier.cleared events for 'dmv' + 1 for 'expunction' → both counted."""
    _seed_session(db_path, "sid-1")
    mid = _NOW_SUNDAY - timedelta(days=2)
    _insert_outcome(
        db_path, "sid-1", "barrier.cleared",
        payload={"barrier_id": "dmv"}, created_at=mid,
    )
    _insert_outcome(
        db_path, "sid-1", "barrier.cleared",
        payload={"barrier_id": "dmv"}, created_at=mid,
    )
    _insert_outcome(
        db_path, "sid-1", "barrier.cleared",
        payload={"barrier_id": "expunction"}, created_at=mid,
    )
    from app.modules.plan.weekly_review import build_weekly_review

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    assert review.barriers_cleared.total == 3
    assert review.barriers_cleared.by_barrier == {"dmv": 2, "expunction": 1}


def test_barriers_cleared_uses_barrier_resolved_too(db_path: str) -> None:
    """Dual event_type handling: barrier_resolved counted alongside barrier.cleared."""
    _seed_session(db_path, "sid-1")
    mid = _NOW_SUNDAY - timedelta(days=1)
    _insert_outcome(
        db_path, "sid-1", "barrier.cleared",
        payload={"barrier_id": "dmv"}, created_at=mid,
    )
    _insert_outcome(
        db_path, "sid-1", "barrier_resolved",
        payload={"barrier_id": "id"}, created_at=mid,
    )
    from app.modules.plan.weekly_review import build_weekly_review

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    assert review.barriers_cleared.total == 2
    assert review.barriers_cleared.by_barrier == {"dmv": 1, "id": 1}


def test_events_outside_window_excluded(db_path: str) -> None:
    """Outcomes and engagement events outside window are NOT counted."""
    _seed_session(db_path, "sid-1", email="worker@example.com")
    before = _NOW_SUNDAY - timedelta(days=30)
    after = _NOW_SUNDAY + timedelta(days=2)
    _insert_outcome(
        db_path, "sid-1", "job_application_applied", created_at=before,
    )
    _insert_outcome(
        db_path, "sid-1", "job_application_applied", created_at=after,
    )
    _insert_engagement_event(db_path, "sid-1", "digest_sent", created_at=before)
    _insert_sendgrid_event(db_path, "worker@example.com", "open", created_at=after)
    from app.modules.plan.weekly_review import build_weekly_review

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    assert review.funnel_movement.draft_to_applied == 0
    assert review.engagement_trend.digests_sent == 0
    assert review.engagement_trend.digests_opened == 0


# -------------------- Markdown rendering tests --------------------


def test_format_summary_report_renders_all_sections(db_path: str) -> None:
    """Rendered markdown includes headers for all 3 sections + window label."""
    _seed_session(db_path, "sid-1", email="worker@example.com")
    mid = _NOW_SUNDAY - timedelta(days=2)
    _insert_outcome(
        db_path, "sid-1", "job_application_applied", created_at=mid,
    )
    _insert_engagement_event(db_path, "sid-1", "digest_sent", created_at=mid)
    _insert_sendgrid_event(db_path, "worker@example.com", "open", created_at=mid)
    _insert_outcome(
        db_path, "sid-1", "barrier.cleared",
        payload={"barrier_id": "dmv"}, created_at=mid,
    )
    from app.modules.plan.weekly_review import (
        build_weekly_review,
        format_summary_report,
    )

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    md = format_summary_report(review)
    assert "Funnel" in md or "funnel" in md.lower()
    assert "Engagement" in md or "engagement" in md.lower()
    assert "Barrier" in md or "barrier" in md.lower()
    # Window dates present in some form
    assert "2026-04" in md


def test_format_summary_report_handles_empty_review(db_path: str) -> None:
    """Empty review renders a recognizable 'quiet week' message."""
    _seed_session(db_path, "sid-1")
    from app.modules.plan.weekly_review import (
        build_weekly_review,
        format_summary_report,
    )

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    md = format_summary_report(review)
    assert "quiet week" in md.lower()


def test_weekly_review_summary_markdown_matches_format(db_path: str) -> None:
    """`review.summary_markdown` equals `format_summary_report(review)`."""
    _seed_session(db_path, "sid-1")
    from app.modules.plan.weekly_review import (
        build_weekly_review,
        format_summary_report,
    )

    review = build_weekly_review(
        "sid-1",
        (_WINDOW_START, _FOR_DATE_SUNDAY),
        db_path=db_path,
    )
    assert review.summary_markdown == format_summary_report(review)


# -------------------- Scope sentinel --------------------


def test_module_docstring_notes_k_anonymity_scope() -> None:
    """Defensive: module docstring documents per-session scope so future
    contributors don't reach for cross-session aggregation here."""
    import app.modules.plan.weekly_review as wr

    assert wr.__doc__ is not None
    assert "per-session" in wr.__doc__.lower()
    assert "k-anonymity" in wr.__doc__.lower()


# -------------------- Orchestrator (Sunday branch) --------------------


def _install_retro_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import date as _date
    from app.modules.plan.daily_progress import RetroResult

    def _fake_retro(session_id, for_date, *, db_path):
        return RetroResult(
            session_id=session_id,
            for_date=for_date if isinstance(for_date, _date) else _date.today(),
            actions=[], completion_ratio=0.0, summary="stub",
        )
    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "run_nightly_retro", _fake_retro)


def _install_compose_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.engagement.digest_composer import DigestResult

    def _fake_compose(session_id, for_date, *, db_path, city=None, now=None):
        return DigestResult(
            subject=f"digest-{session_id}",
            html="<p>body</p>",
            text="body",
            section_counts={"yesterday": 0, "today": 0, "week": 0, "stall": 0},
        )
    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "compose_digest", _fake_compose)


def _install_send_digest_spy(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    calls: list[dict] = []

    def _fake_send_digest(
        session_id, to_email, subject, html, text, *, db_path=None, now=None,
    ):
        calls.append({
            "session_id": session_id, "to": to_email,
            "subject": subject, "html": html, "text": text,
        })
        from app.modules.engagement.reminder_engine import ReminderDispatchResult
        return ReminderDispatchResult(
            success=True, skipped_reason=None,
            category="digest", message_id="mid",
        )
    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "send_digest", _fake_send_digest)
    return calls


@pytest.mark.anyio
async def test_sunday_orchestrator_invokes_weekly_review(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sunday run → build_weekly_review is called for each session."""
    _seed_session(db_path, "sid-1")
    _install_retro_stub(monkeypatch)
    _install_compose_stub(monkeypatch)
    _install_send_digest_spy(monkeypatch)

    import scripts.nightly_digest as nd
    wr_mod = importlib.import_module("app.modules.plan.weekly_review")
    called: list[dict] = []

    def _fake_build(session_id, date_range, *, db_path):
        called.append({"session_id": session_id, "date_range": date_range})
        return wr_mod.WeeklyReview(
            session_id=session_id,
            window_start=date_range[0],
            window_end=date_range[1],
            funnel_movement=wr_mod.FunnelMovement(0, 0, 0),
            engagement_trend=wr_mod.EngagementTrend(0, 0, None, 0),
            barriers_cleared=wr_mod.BarriersClearedSummary(0, {}),
            summary_markdown="quiet week stub",
        )
    monkeypatch.setattr(nd.weekly_review, "build_weekly_review", _fake_build)

    from scripts.nightly_digest import run_nightly_digest
    await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW_SUNDAY,
    )
    assert len(called) == 1
    assert called[0]["session_id"] == "sid-1"


@pytest.mark.anyio
async def test_non_sunday_skips_weekly_review(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Monday run → build_weekly_review is NOT called."""
    _seed_session(db_path, "sid-1")
    _install_retro_stub(monkeypatch)
    _install_compose_stub(monkeypatch)
    _install_send_digest_spy(monkeypatch)

    import scripts.nightly_digest as nd
    called: list[dict] = []

    def _fake_build(session_id, date_range, *, db_path):
        called.append({"session_id": session_id})
        raise AssertionError("weekly review must not run on non-Sunday")
    monkeypatch.setattr(nd.weekly_review, "build_weekly_review", _fake_build)

    from scripts.nightly_digest import run_nightly_digest
    await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW_MONDAY,
    )
    assert called == []


@pytest.mark.anyio
async def test_sunday_sends_two_emails(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sunday → send_digest called twice (daily + weekly) with distinct subjects."""
    _seed_session(db_path, "sid-1")
    _install_retro_stub(monkeypatch)
    _install_compose_stub(monkeypatch)
    sent = _install_send_digest_spy(monkeypatch)

    import scripts.nightly_digest as nd
    wr_mod = importlib.import_module("app.modules.plan.weekly_review")

    def _fake_build(session_id, date_range, *, db_path):
        return wr_mod.WeeklyReview(
            session_id=session_id,
            window_start=date_range[0],
            window_end=date_range[1],
            funnel_movement=wr_mod.FunnelMovement(0, 0, 0),
            engagement_trend=wr_mod.EngagementTrend(0, 0, None, 0),
            barriers_cleared=wr_mod.BarriersClearedSummary(0, {}),
            summary_markdown="weekly body",
        )
    monkeypatch.setattr(nd.weekly_review, "build_weekly_review", _fake_build)

    from scripts.nightly_digest import run_nightly_digest
    await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW_SUNDAY,
    )
    assert len(sent) == 2
    subjects = sorted(c["subject"] for c in sent)
    # Weekly subject distinct from daily (e.g., "Your week" marker).
    assert any("week" in s.lower() for s in subjects)
    assert any("digest" in s.lower() for s in subjects)
