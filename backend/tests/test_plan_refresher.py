"""Tests for plan_refresher + plan_progress (T12.24, S12b).

Covers:
- merge_existing_progress preserves checklist state for matching action keys
- _extract_progress reads sessions.action_checklist into a normalized dict
- refresh_plan no-op when neither HARD stall nor breakthrough is present
- refresh_plan triggered by HARD stall: archives + writes new plan
- refresh_plan triggered by breakthrough (recent barrier_resolved outcome)
- Dual-write to sessions.previous_plan (S12b only — slated for S13 deprecation)
- plan_history capped at 20 rows per session (oldest deleted on overflow)
- refresh_reason + triggering_event recorded on plan_history rows
- calibrated_weeks consumed from intelligence engine when refreshing
- Nightly orchestrator wires refresh_plan in place of the S12a TODO stub
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from app.modules.plan import plan_refresher
from app.modules.plan.plan_progress import (
    _extract_progress,
    load_existing_progress,
    merge_existing_progress,
)
from app.modules.plan.plan_refresher import RefreshResult, refresh_plan

# Module under test — imported lazily inside tests so the first run surfaces
# ImportError during the RED phase of TDD.

_NOW = datetime(2026, 4, 23, 2, 0, tzinfo=timezone.utc)
_SESSION_ID = "11111111-1111-1111-1111-111111111111"


# -------------------- Fixtures --------------------


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "refresher.db")
    runner.apply_pending(path)
    return path


def _seed_session(
    db_path: str,
    session_id: str = _SESSION_ID,
    *,
    barriers: list[str] | None = None,
    plan: dict | None = None,
    action_checklist: dict | None = None,
    previous_plan: dict | None = None,
    benefits_profile: dict | None = None,
) -> None:
    """Insert one sessions row with optional plan/checklist/profile JSON."""
    expires = (_NOW + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, plan, "
            "action_checklist, previous_plan, benefits_profile, "
            "profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                _NOW.isoformat(),
                json.dumps(barriers or ["credit", "transportation"]),
                json.dumps(plan) if plan is not None else None,
                json.dumps(action_checklist) if action_checklist is not None else None,
                json.dumps(previous_plan) if previous_plan is not None else None,
                json.dumps(benefits_profile or {}),
                json.dumps({"first_name": "Worker"}),
                expires,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _make_plan(action_keys: list[str]) -> dict:
    """Build a minimal ActionPlan-shaped dict from a list of action keys."""
    actions = [
        {
            "category": "credit_repair",
            "title": key,
            "detail": None,
            "priority": 0,
            "source_module": "credit",
            "resource_name": None,
            "resource_phone": None,
            "resource_address": None,
        }
        for key in action_keys
    ]
    return {
        "assessment_date": "2026-04-20",
        "phases": [
            {
                "phase_id": "week_1_2",
                "label": "Week 1-2",
                "start_day": 0,
                "end_day": 14,
                "actions": actions,
            },
        ],
        "total_actions": len(actions),
    }


def _insert_outcome(
    db_path: str, session_id: str, event_type: str, *, when: datetime,
    payload: dict | None = None,
) -> None:
    """Append an outcomes_records row (used to seed breakthrough signals)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                session_id,
                event_type,
                json.dumps(payload or {}),
                when.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _read_history(db_path: str, session_id: str) -> list[dict]:
    """Return plan_history rows for a session (most-recent first)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, archived_at, plan_json, refresh_reason, "
            "triggering_event FROM plan_history "
            "WHERE session_id = ? ORDER BY archived_at DESC, id DESC",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def _read_session_plan(db_path: str, session_id: str) -> tuple[dict | None, dict | None]:
    """Return (plan, previous_plan) JSON for a session."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT plan, previous_plan FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    plan = json.loads(row[0]) if row and row[0] else None
    prev = json.loads(row[1]) if row and row[1] else None
    return plan, prev


# -------------------- plan_progress tests --------------------


def test_extract_progress_returns_empty_when_no_checklist(db_path: str) -> None:
    """No action_checklist row → extract returns empty checklist dict."""
    plan = _make_plan(["activate-credit-karma"])
    progress = _extract_progress(plan, action_checklist={})

    assert progress["checklist"] == {}


def test_extract_progress_keys_by_phase_category_title() -> None:
    """Checklist entries are keyed by (phase_id, category, title) triple."""
    plan = _make_plan(["activate-credit-karma"])
    checklist = {
        "week_1_2|credit_repair|activate-credit-karma": {
            "completed": True,
            "completed_at": "2026-04-21T10:00:00Z",
            "notes": "did it",
        },
        "week_1_2|credit_repair|stale-key": {"completed": True},
    }

    progress = _extract_progress(plan, action_checklist=checklist)

    assert "week_1_2|credit_repair|activate-credit-karma" in progress["checklist"]
    assert progress["checklist"][
        "week_1_2|credit_repair|activate-credit-karma"
    ]["completed"] is True


def test_load_existing_progress_reads_session_row(db_path: str) -> None:
    """load_existing_progress fetches plan + checklist from sessions row."""
    plan = _make_plan(["pull-credit-report"])
    checklist = {
        "week_1_2|credit_repair|pull-credit-report": {"completed": True},
    }
    _seed_session(db_path, plan=plan, action_checklist=checklist)

    progress = load_existing_progress(_SESSION_ID, db_path=db_path)

    assert progress["checklist"][
        "week_1_2|credit_repair|pull-credit-report"
    ]["completed"] is True


def test_merge_existing_progress_preserves_completed_state() -> None:
    """Items present in old progress and new plan keep their completed state."""
    new_plan = _make_plan(["pull-credit-report", "new-action"])
    progress = {
        "checklist": {
            "week_1_2|credit_repair|pull-credit-report": {
                "completed": True,
                "completed_at": "2026-04-22T09:00:00Z",
            },
        },
    }

    merged = merge_existing_progress(new_plan, progress)

    pull_key = "week_1_2|credit_repair|pull-credit-report"
    new_key = "week_1_2|credit_repair|new-action"
    assert merged[pull_key]["completed"] is True
    assert merged[pull_key]["completed_at"] == "2026-04-22T09:00:00Z"
    # New action present but not completed
    assert merged[new_key]["completed"] is False


def test_merge_drops_keys_absent_from_new_plan() -> None:
    """Stale checklist keys (item removed from new plan) do not survive."""
    new_plan = _make_plan(["fresh-action"])
    progress = {
        "checklist": {
            "week_1_2|credit_repair|removed-action": {"completed": True},
        },
    }

    merged = merge_existing_progress(new_plan, progress)

    assert "week_1_2|credit_repair|removed-action" not in merged
    assert "week_1_2|credit_repair|fresh-action" in merged


# -------------------- refresh_plan trigger tests --------------------


def test_refresh_no_trigger_returns_skip_result(db_path: str) -> None:
    """No HARD stall and no breakthrough → no refresh, no archive."""
    plan = _make_plan(["pull-credit-report"])
    _seed_session(db_path, plan=plan)

    result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

    assert result.refreshed is False
    assert result.trigger_reason is None
    assert _read_history(db_path, _SESSION_ID) == []


def test_refresh_triggered_by_explicit_trigger_reason(db_path: str) -> None:
    """An explicit trigger_reason argument bypasses the auto-detect path."""
    plan = _make_plan(["pull-credit-report"])
    _seed_session(db_path, plan=plan)

    result = refresh_plan(
        _SESSION_ID, db_path=db_path, trigger_reason="manual", now=_NOW,
    )

    assert result.refreshed is True
    assert result.trigger_reason == "manual"
    history = _read_history(db_path, _SESSION_ID)
    assert len(history) == 1
    assert history[0]["refresh_reason"] == "manual"


def test_refresh_triggered_by_hard_stall(monkeypatch: pytest.MonkeyPatch, db_path: str) -> None:
    """HARD stall_level reported by the detector triggers a refresh."""
    from app.modules.common.temporal_types import StallLevel
    from app.modules.engagement import stall_detector
    plan = _make_plan(["pull-credit-report"])
    _seed_session(db_path, plan=plan)

    fake = stall_detector.StalledSession(
        session_id=_SESSION_ID,
        stalled_barriers=[],
        days_stalled=15,
        stall_level=StallLevel.HARD,
    )
    monkeypatch.setattr(
        plan_refresher, "compute_stall_for_session",
        lambda sid, **kw: fake,
    )

    result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

    assert result.refreshed is True
    assert result.trigger_reason == "stall_hard"
    assert result.triggering_event is not None
    assert "hard" in result.triggering_event.lower()


def test_refresh_triggered_by_breakthrough_outcome(db_path: str) -> None:
    """A recent barrier_resolved outcome triggers a refresh (breakthrough)."""
    plan = _make_plan(["pull-credit-report"])
    _seed_session(db_path, plan=plan)

    # Breakthrough = barrier_resolved within the last 24h
    _insert_outcome(
        db_path, _SESSION_ID, "barrier_resolved",
        when=_NOW - timedelta(hours=2),
        payload={"barrier_id": "credit"},
    )

    result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

    assert result.refreshed is True
    assert result.trigger_reason == "breakthrough"
    assert result.triggering_event is not None
    assert "barrier_resolved" in result.triggering_event


def test_refresh_ignores_stale_breakthrough(db_path: str) -> None:
    """A barrier_resolved outcome older than the breakthrough window is ignored."""
    plan = _make_plan(["pull-credit-report"])
    _seed_session(db_path, plan=plan)
    # Outside 24h window
    _insert_outcome(
        db_path, _SESSION_ID, "barrier_resolved",
        when=_NOW - timedelta(days=7),
        payload={"barrier_id": "credit"},
    )

    result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

    assert result.refreshed is False


# -------------------- archive + dual-write tests --------------------


def test_refresh_dual_writes_previous_plan(db_path: str) -> None:
    """sessions.previous_plan mirrors the archived plan (S13 deprecation slated)."""
    old_plan = _make_plan(["pull-credit-report"])
    _seed_session(db_path, plan=old_plan)

    refresh_plan(
        _SESSION_ID, db_path=db_path, trigger_reason="manual", now=_NOW,
    )

    new_plan, prev_plan = _read_session_plan(db_path, _SESSION_ID)
    assert prev_plan == old_plan
    # The new plan replaces the old plan column
    assert new_plan is not None
    assert new_plan != old_plan


def test_refresh_archive_records_reason_and_event(db_path: str) -> None:
    """plan_history row carries both refresh_reason and triggering_event."""
    plan = _make_plan(["pull-credit-report"])
    _seed_session(db_path, plan=plan)

    refresh_plan(
        _SESSION_ID, db_path=db_path,
        trigger_reason="stall_hard",
        triggering_event="stall_level=hard;days=15",
        now=_NOW,
    )

    history = _read_history(db_path, _SESSION_ID)
    assert history[0]["refresh_reason"] == "stall_hard"
    assert history[0]["triggering_event"] == "stall_level=hard;days=15"


# -------------------- 20-row cap test --------------------


def test_plan_history_capped_at_20_per_session(db_path: str) -> None:
    """After the 21st refresh, only the 20 newest rows remain for that session."""
    _seed_session(db_path, plan=_make_plan(["pull-credit-report"]))

    # 21 refreshes — each archives the current plan to history
    for i in range(21):
        # bump now so archived_at differs
        ts = _NOW + timedelta(minutes=i)
        refresh_plan(
            _SESSION_ID, db_path=db_path,
            trigger_reason=f"manual-{i}",
            now=ts,
        )

    history = _read_history(db_path, _SESSION_ID)
    assert len(history) == 20
    # The oldest reason ("manual-0") must be evicted
    reasons = {row["refresh_reason"] for row in history}
    assert "manual-0" not in reasons
    assert "manual-20" in reasons


def test_plan_history_cap_isolates_other_sessions(db_path: str) -> None:
    """The 20-row cap is per-session — other sessions are untouched."""
    other = "22222222-2222-2222-2222-222222222222"
    _seed_session(db_path, _SESSION_ID, plan=_make_plan(["a"]))
    _seed_session(db_path, other, plan=_make_plan(["b"]))

    # 21 refreshes of session A
    for i in range(21):
        ts = _NOW + timedelta(minutes=i)
        refresh_plan(
            _SESSION_ID, db_path=db_path,
            trigger_reason=f"a-{i}", now=ts,
        )
    # 1 refresh of session B
    refresh_plan(
        other, db_path=db_path, trigger_reason="b-0", now=_NOW,
    )

    assert len(_read_history(db_path, _SESSION_ID)) == 20
    assert len(_read_history(db_path, other)) == 1


# -------------------- calibrated_weeks integration test --------------------


def test_refresh_passes_calibrated_weeks_to_pathway(
    monkeypatch: pytest.MonkeyPatch, db_path: str,
) -> None:
    """refresh_plan reads calibrated_weeks and forwards them to the pathway engine."""
    _seed_session(db_path, plan=_make_plan(["a"]))

    # Stub the calibration accessor
    monkeypatch.setattr(
        plan_refresher, "load_calibrated_weeks",
        lambda db_path: {"credit": 9, "transportation": 12},
    )

    captured: dict = {}

    def _spy_generate_pathways(
        barrier_ids, benefits_profile, current_wage, calibrated_weeks=None,
    ):
        captured["calibrated_weeks"] = calibrated_weeks
        captured["barrier_ids"] = list(barrier_ids)
        # Return a minimal PathwayResult-shaped dict-like via the real type
        from app.modules.pathway.types import PathwayResult
        return PathwayResult(
            pathways=[],
            current_wage=current_wage,
            current_net_monthly=0.0,
            barriers_active=list(barrier_ids),
        )

    monkeypatch.setattr(
        plan_refresher, "generate_pathways", _spy_generate_pathways,
    )

    refresh_plan(
        _SESSION_ID, db_path=db_path, trigger_reason="manual", now=_NOW,
    )

    assert captured["calibrated_weeks"] == {"credit": 9, "transportation": 12}
    assert "credit" in captured["barrier_ids"]


# -------------------- nightly orchestrator wiring --------------------


def _seed_montgomery_session_for_orchestrator(db_path: str) -> None:
    """Seed one active session tagged to montgomery for orchestrator tests."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                _SESSION_ID, _NOW.isoformat(), json.dumps(["credit"]),
                json.dumps({"first_name": "W", "email": "w@example.com"}),
                (_NOW + timedelta(days=30)).isoformat(),
            ),
        )
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                _SESSION_ID, "city_tag",
                json.dumps({"city": "montgomery"}), _NOW.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _stub_orchestrator_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch retro/compose/send so the orchestrator runs without real DB or SMTP."""
    from datetime import date as _date

    from app.modules.engagement.digest_composer import DigestResult
    from app.modules.engagement.reminder_engine import ReminderDispatchResult
    from app.modules.plan.daily_progress import RetroResult

    import scripts.nightly_digest as nd
    monkeypatch.setattr(
        nd, "run_nightly_retro",
        lambda sid, fd, *, db_path: RetroResult(
            session_id=sid, for_date=fd if isinstance(fd, _date) else _date.today(),
            actions=[], completion_ratio=0.0, summary="stub",
        ),
    )
    monkeypatch.setattr(
        nd, "compose_digest",
        lambda sid, fd, *, db_path, city=None, now=None: DigestResult(
            subject="s", html="<p>x</p>", text="x",
            section_counts={"yesterday": 0, "today": 0, "week": 0, "stall": 0},
        ),
    )
    monkeypatch.setattr(
        nd, "send_digest",
        lambda sid, em, sub, html, text, *, db_path=None, now=None:
        ReminderDispatchResult(
            success=True, skipped_reason=None,
            category="digest", message_id="m",
        ),
    )


def test_nightly_orchestrator_invokes_refresh_plan(
    monkeypatch: pytest.MonkeyPatch, db_path: str,
) -> None:
    """The nightly_digest pipeline calls refresh_plan in place of the S12a stub."""
    _seed_montgomery_session_for_orchestrator(db_path)
    _stub_orchestrator_pipeline(monkeypatch)

    calls: list[dict] = []

    def _spy_refresh(session_id, *, db_path, now=None, trigger_reason=None):
        calls.append({"session_id": session_id})
        return RefreshResult(refreshed=False)

    import scripts.nightly_digest as nd
    monkeypatch.setattr(nd, "refresh_plan", _spy_refresh)

    asyncio.run(nd.run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    ))

    assert any(c["session_id"] == _SESSION_ID for c in calls)
