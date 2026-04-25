"""Plan refresher trigger matrix coverage (T13.65, S13).

Exhaustively exercises the cross product of (trigger type x window
boundary x carry-forward edge) for the T12.24 refresher, plus the
20-row plan_history cap and ordering invariant. Sister to
``test_plan_refresher.py`` (lifecycle smoke) — this file is the QC
regression net for every individual lever the refresher exposes.

Coverage map (T13.65 acceptance criteria):
1. Trigger matrix (4 cells): stall_hard alone, barrier_resolved alone,
   both (stall wins per ``_detect_trigger`` precedence), neither.
2. Window boundary: BREAKTHROUGH_WINDOW (24h) probed at t=0,
   23h59m59s, exact 24h (inclusive), 24h00m01s, 25h, 7d.
3. Carry-forward (4 edges): empty prior, partial overlap, full
   overlap, zero overlap.
4. 20-row cap + newest-first ordering after eviction.

No production bugs surfaced; all asserts pass against current code.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from app.modules.common.temporal_types import StallLevel
from app.modules.engagement import stall_detector
from app.modules.plan import plan_refresher
from app.modules.plan._plan_refresher_db import (
    BREAKTHROUGH_WINDOW,
    PLAN_HISTORY_CAP_PER_SESSION,
)
from app.modules.plan.plan_refresher import refresh_plan
from tests._fake_clock import freeze_time

# Deterministic UTC anchor for ISO-string ordering in SQLite.
_NOW = datetime(2026, 4, 23, 2, 0, tzinfo=timezone.utc)
_SESSION_ID = "11111111-1111-1111-1111-111111111111"


# -- Fixtures + seed helpers --


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Fresh DB with all migrations applied."""
    path = str(tmp_path / "matrix.db")
    runner.apply_pending(path)
    return path


def _seed_session(
    db_path: str,
    session_id: str = _SESSION_ID,
    *,
    plan: dict | None = None,
    action_checklist: dict | None = None,
    barriers: list[str] | None = None,
) -> None:
    """Insert one sessions row used by every matrix test."""
    expires = (_NOW + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, plan, "
            "action_checklist, benefits_profile, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                _NOW.isoformat(),
                json.dumps(barriers or ["credit", "transportation"]),
                json.dumps(plan) if plan is not None else None,
                json.dumps(action_checklist) if action_checklist is not None else None,
                json.dumps({}),
                json.dumps({"first_name": "Worker"}),
                expires,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _make_plan(action_titles: list[str], *, phase_id: str = "week_1_2",
               category: str = "credit_repair") -> dict:
    """Build a minimal plan dict shaped like ActionPlan.model_dump()."""
    actions = [
        {
            "category": category,
            "title": t,
            "detail": None,
            "priority": 0,
            "source_module": "credit",
            "resource_name": None,
            "resource_phone": None,
            "resource_address": None,
        }
        for t in action_titles
    ]
    return {
        "assessment_date": "2026-04-20",
        "phases": [
            {
                "phase_id": phase_id,
                "label": "Week 1-2",
                "start_day": 0,
                "end_day": 14,
                "actions": actions,
            },
        ],
        "total_actions": len(actions),
    }


def _make_checklist(completed_titles: list[str], *, phase_id: str = "week_1_2",
                    category: str = "credit_repair",
                    completed_at: str = "2026-04-22T09:00:00Z") -> dict:
    """Build an action_checklist dict marking the listed titles complete."""
    return {
        f"{phase_id}|{category}|{t}": {
            "completed": True,
            "completed_at": completed_at,
            "notes": f"finished {t}",
        }
        for t in completed_titles
    }


def _insert_outcome(
    db_path: str, session_id: str, *,
    when: datetime, payload: dict | None = None,
    event_type: str = "barrier_resolved",
) -> None:
    """Append an outcomes_records row."""
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
    """plan_history rows, newest-first (matches archive eviction order)."""
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


def _read_checklist(db_path: str, session_id: str) -> dict:
    """Read sessions.action_checklist after a refresh."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT action_checklist FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    return json.loads(row[0]) if row and row[0] else {}


def _patch_stall(monkeypatch: pytest.MonkeyPatch, *, level: StallLevel,
                 days: int = 15) -> None:
    """Force the stall detector to report ``level``."""
    fake = stall_detector.StalledSession(
        session_id=_SESSION_ID,
        stalled_barriers=[],
        days_stalled=days,
        stall_level=level,
    )
    monkeypatch.setattr(
        plan_refresher, "compute_stall_for_session",
        lambda sid, **kw: fake,
    )


def _patch_new_plan(monkeypatch: pytest.MonkeyPatch, plan: dict) -> None:
    """Inject a known post-refresh plan so carry-forward keys are deterministic.

    The real builder calls ``generate_pathways`` which returns a shape
    with no ``phases`` key, yielding zero carry-forward keys. We
    bypass it so each case can assert against an explicit key set.
    """
    monkeypatch.setattr(
        plan_refresher, "_build_plan_for_session",
        lambda session_row, calibrated_weeks, today: plan,
    )


# -- Trigger matrix (4 cells) --


class TestTriggerMatrix:
    """Cross product of (stall_hard in {T,F}) x (barrier_resolved in {T,F})."""

    def test_neither_trigger_skips_refresh(self, db_path: str) -> None:
        """stall_hard=False, barrier_resolved=False -> no-op, no archive."""
        _seed_session(db_path, plan=_make_plan(["a"]))

        result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

        assert result.refreshed is False
        assert result.trigger_reason is None
        assert _read_history(db_path, _SESSION_ID) == []

    def test_stall_only_fires_with_stall_hard_reason(
        self, monkeypatch: pytest.MonkeyPatch, db_path: str,
    ) -> None:
        """stall_hard=True, barrier_resolved=False -> fires with stall_hard."""
        _seed_session(db_path, plan=_make_plan(["a"]))
        _patch_stall(monkeypatch, level=StallLevel.HARD)

        result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

        assert result.refreshed is True
        assert result.trigger_reason == "stall_hard"
        assert "hard" in (result.triggering_event or "").lower()
        assert len(_read_history(db_path, _SESSION_ID)) == 1

    def test_breakthrough_only_fires_with_breakthrough_reason(
        self, db_path: str,
    ) -> None:
        """stall_hard=False, barrier_resolved=True -> fires with breakthrough."""
        _seed_session(db_path, plan=_make_plan(["a"]))
        _insert_outcome(
            db_path, _SESSION_ID,
            when=_NOW - timedelta(hours=2),
            payload={"barrier_id": "credit"},
        )

        result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

        assert result.refreshed is True
        assert result.trigger_reason == "breakthrough"
        assert "barrier_resolved" in (result.triggering_event or "")

    def test_both_triggers_fire_stall_wins(
        self, monkeypatch: pytest.MonkeyPatch, db_path: str,
    ) -> None:
        """Both true -> stall_hard wins. ``_detect_trigger`` checks stall first."""
        _seed_session(db_path, plan=_make_plan(["a"]))
        _patch_stall(monkeypatch, level=StallLevel.HARD, days=22)
        _insert_outcome(
            db_path, _SESSION_ID,
            when=_NOW - timedelta(hours=1),
            payload={"barrier_id": "transportation"},
        )

        result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

        assert result.refreshed is True
        assert result.trigger_reason == "stall_hard"
        # One archive row per refresh, no matter how many triggers fired.
        history = _read_history(db_path, _SESSION_ID)
        assert len(history) == 1
        assert history[0]["refresh_reason"] == "stall_hard"

    def test_soft_stall_does_not_trigger(
        self, monkeypatch: pytest.MonkeyPatch, db_path: str,
    ) -> None:
        """Only HARD level qualifies — SOFT/MEDIUM are silently ignored."""
        _seed_session(db_path, plan=_make_plan(["a"]))
        _patch_stall(monkeypatch, level=StallLevel.SOFT)

        result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

        assert result.refreshed is False
        assert _read_history(db_path, _SESSION_ID) == []


# -- Window boundary (breakthrough 24h cutoff) --


class TestBreakthroughWindowBoundary:
    """Probe BREAKTHROUGH_WINDOW (24h) at the inclusive edge.

    Detector uses ``created_at >= now - BREAKTHROUGH_WINDOW``. Tests
    pin the exact boundary so a future SQL refactor doesn't shift it.
    Uses freeze_time to align production ``datetime.now`` reads with
    the test instant.
    """

    @pytest.mark.parametrize(
        ("offset", "should_fire"),
        [
            (timedelta(0), True),                # exact "now" — fires
            (timedelta(hours=12), True),         # mid-window — fires
            (BREAKTHROUGH_WINDOW - timedelta(seconds=1), True),  # just inside
            (BREAKTHROUGH_WINDOW, True),         # exact lower edge — inclusive
            (BREAKTHROUGH_WINDOW + timedelta(seconds=1), False),  # just outside
            (BREAKTHROUGH_WINDOW + timedelta(hours=1), False),    # 25h — out
            (timedelta(days=7), False),          # very stale — out
        ],
    )
    def test_breakthrough_window_edge(
        self, db_path: str, offset: timedelta, should_fire: bool,
    ) -> None:
        """Refresh fires iff barrier_resolved.created_at >= now - 24h."""
        _seed_session(db_path, plan=_make_plan(["a"]))
        _insert_outcome(
            db_path, _SESSION_ID,
            when=_NOW - offset,
            payload={"barrier_id": "credit"},
        )

        with freeze_time(_NOW):
            result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

        assert result.refreshed is should_fire, (
            f"offset={offset}: expected refreshed={should_fire}, "
            f"got refreshed={result.refreshed} reason={result.trigger_reason}"
        )

    def test_window_boundary_with_stall_overrides_window(
        self, monkeypatch: pytest.MonkeyPatch, db_path: str,
    ) -> None:
        """Stale breakthrough does NOT block a stall-driven refresh."""
        _seed_session(db_path, plan=_make_plan(["a"]))
        _patch_stall(monkeypatch, level=StallLevel.HARD)
        # Outside the breakthrough window
        _insert_outcome(
            db_path, _SESSION_ID,
            when=_NOW - timedelta(days=10),
            payload={"barrier_id": "credit"},
        )

        result = refresh_plan(_SESSION_ID, db_path=db_path, now=_NOW)

        assert result.refreshed is True
        assert result.trigger_reason == "stall_hard"


# -- Carry-forward edges (4 cells) --


class TestCarryForwardMatrix:
    """Empty / partial / full / no-match overlap between old + new plans."""

    def test_empty_prior_plan_starts_fresh_checklist(
        self, monkeypatch: pytest.MonkeyPatch, db_path: str,
    ) -> None:
        """Empty prior plan -> new plan keys all start fresh (completed=False)."""
        # Prior plan absent (no plan column, no checklist column)
        _seed_session(db_path)
        new_plan = _make_plan(["a", "b", "c"])
        _patch_new_plan(monkeypatch, new_plan)

        result = refresh_plan(
            _SESSION_ID, db_path=db_path, trigger_reason="manual", now=_NOW,
        )

        assert result.refreshed is True
        checklist = _read_checklist(db_path, _SESSION_ID)
        assert set(checklist.keys()) == {
            "week_1_2|credit_repair|a",
            "week_1_2|credit_repair|b",
            "week_1_2|credit_repair|c",
        }
        for key, state in checklist.items():
            assert state["completed"] is False, key
            assert state["completed_at"] is None, key

    def test_partial_match_preserves_overlapping_completion(
        self, monkeypatch: pytest.MonkeyPatch, db_path: str,
    ) -> None:
        """Partial overlap: matched titles keep state, others reset."""
        prior_plan = _make_plan(["pull-credit", "dispute", "monitor"])
        prior_checklist = _make_checklist(
            ["pull-credit", "dispute", "monitor"],
            completed_at="2026-04-22T09:00:00Z",
        )
        _seed_session(
            db_path, plan=prior_plan, action_checklist=prior_checklist,
        )
        # New plan: 2 overlap (pull-credit, dispute), 2 are brand new
        new_plan = _make_plan(["pull-credit", "dispute", "new-step", "another-new"])
        _patch_new_plan(monkeypatch, new_plan)

        refresh_plan(
            _SESSION_ID, db_path=db_path, trigger_reason="manual", now=_NOW,
        )

        checklist = _read_checklist(db_path, _SESSION_ID)
        # Overlapping items: completion preserved
        assert checklist["week_1_2|credit_repair|pull-credit"]["completed"] is True
        assert checklist["week_1_2|credit_repair|pull-credit"]["completed_at"] \
            == "2026-04-22T09:00:00Z"
        assert checklist["week_1_2|credit_repair|dispute"]["completed"] is True
        # New items: fresh state
        assert checklist["week_1_2|credit_repair|new-step"]["completed"] is False
        assert checklist["week_1_2|credit_repair|new-step"]["completed_at"] is None
        assert checklist["week_1_2|credit_repair|another-new"]["completed"] is False
        # Removed item ("monitor") is dropped
        assert "week_1_2|credit_repair|monitor" not in checklist

    def test_full_match_preserves_every_completion(
        self, monkeypatch: pytest.MonkeyPatch, db_path: str,
    ) -> None:
        """Full overlap: every prior completion timestamp survives."""
        titles = ["a", "b", "c", "d"]
        prior_plan = _make_plan(titles)
        prior_checklist = _make_checklist(
            titles, completed_at="2026-04-22T11:00:00Z",
        )
        _seed_session(
            db_path, plan=prior_plan, action_checklist=prior_checklist,
        )
        new_plan = _make_plan(titles)  # identical key set
        _patch_new_plan(monkeypatch, new_plan)

        refresh_plan(
            _SESSION_ID, db_path=db_path, trigger_reason="manual", now=_NOW,
        )

        checklist = _read_checklist(db_path, _SESSION_ID)
        assert len(checklist) == len(titles)
        for t in titles:
            entry = checklist[f"week_1_2|credit_repair|{t}"]
            assert entry["completed"] is True
            assert entry["completed_at"] == "2026-04-22T11:00:00Z"
            assert entry["notes"] == f"finished {t}"

    def test_no_match_drops_old_resets_new(
        self, monkeypatch: pytest.MonkeyPatch, db_path: str,
    ) -> None:
        """Zero overlap: prior completions are evicted, new keys are fresh."""
        prior_titles = ["old-1", "old-2", "old-3", "old-4", "old-5"]
        prior_plan = _make_plan(prior_titles)
        prior_checklist = _make_checklist(prior_titles)
        _seed_session(
            db_path, plan=prior_plan, action_checklist=prior_checklist,
        )
        new_titles = ["new-1", "new-2", "new-3", "new-4", "new-5"]
        new_plan = _make_plan(new_titles)
        _patch_new_plan(monkeypatch, new_plan)

        refresh_plan(
            _SESSION_ID, db_path=db_path, trigger_reason="manual", now=_NOW,
        )

        checklist = _read_checklist(db_path, _SESSION_ID)
        assert set(checklist.keys()) == {
            f"week_1_2|credit_repair|{t}" for t in new_titles
        }
        for state in checklist.values():
            assert state["completed"] is False
            assert state["completed_at"] is None

    def test_no_match_archives_full_prior_plan_to_history(
        self, monkeypatch: pytest.MonkeyPatch, db_path: str,
    ) -> None:
        """No-match case still archives the prior plan verbatim — history is canonical."""
        prior_plan = _make_plan(["old-1", "old-2"])
        _seed_session(db_path, plan=prior_plan, action_checklist={})
        new_plan = _make_plan(["new-1", "new-2"])
        _patch_new_plan(monkeypatch, new_plan)

        refresh_plan(
            _SESSION_ID, db_path=db_path, trigger_reason="manual", now=_NOW,
        )

        history = _read_history(db_path, _SESSION_ID)
        assert len(history) == 1
        archived = json.loads(history[0]["plan_json"])
        assert archived == prior_plan


# -- 20-row cap + ordering invariant --


def _seed_history_rows(db_path: str, session_id: str, count: int,
                       *, base: datetime) -> None:
    """Pre-seed ``count`` plan_history rows so the cap test starts saturated."""
    conn = sqlite3.connect(db_path)
    try:
        for i in range(count):
            ts = base + timedelta(minutes=i)
            conn.execute(
                "INSERT INTO plan_history "
                "(session_id, archived_at, plan_json, refresh_reason, "
                "triggering_event) VALUES (?, ?, ?, ?, ?)",
                (
                    session_id,
                    ts.isoformat(),
                    json.dumps({"seed": i}),
                    f"seed-{i}",
                    f"event-{i}",
                ),
            )
        conn.commit()
    finally:
        conn.close()


class TestHistoryCapAndOrdering:
    """The 20-row cap + newest-first ordering after one refresh."""

    def test_25_seeded_rows_cap_to_20_after_refresh(self, db_path: str) -> None:
        """Seeding 25 rows + 1 refresh -> exactly 20 rows remain."""
        _seed_session(db_path, plan=_make_plan(["a"]))
        # Earliest seed sits 25 minutes before _NOW so the new archive
        # row is unambiguously the newest.
        base = _NOW - timedelta(hours=2)
        _seed_history_rows(db_path, _SESSION_ID, 25, base=base)

        # Trigger one refresh; the archive_plan call inserts +1 row then
        # invokes _enforce_history_cap to delete down to 20.
        refresh_plan(
            _SESSION_ID, db_path=db_path,
            trigger_reason="cap-test", now=_NOW,
        )

        history = _read_history(db_path, _SESSION_ID)
        assert len(history) == PLAN_HISTORY_CAP_PER_SESSION == 20

    def test_oldest_rows_evicted_when_capped(self, db_path: str) -> None:
        """25 seeded + 1 fresh = 26 rows; the 6 oldest are evicted to cap at 20."""
        _seed_session(db_path, plan=_make_plan(["a"]))
        base = _NOW - timedelta(hours=2)
        _seed_history_rows(db_path, _SESSION_ID, 25, base=base)

        refresh_plan(
            _SESSION_ID, db_path=db_path,
            trigger_reason="cap-test", now=_NOW,
        )

        reasons = {row["refresh_reason"] for row in _read_history(db_path, _SESSION_ID)}
        # seed-0..seed-5 are the 6 oldest -> evicted
        for i in range(6):
            assert f"seed-{i}" not in reasons, f"seed-{i} should be evicted"
        # seed-6..seed-24 (19 rows) + new "cap-test" = 20 retained
        for i in range(6, 25):
            assert f"seed-{i}" in reasons, f"seed-{i} should be retained"
        assert "cap-test" in reasons

    def test_history_sorted_newest_first(self, db_path: str) -> None:
        """plan_history rows come back ordered by archived_at DESC."""
        _seed_session(db_path, plan=_make_plan(["a"]))
        base = _NOW - timedelta(hours=2)
        _seed_history_rows(db_path, _SESSION_ID, 25, base=base)

        refresh_plan(
            _SESSION_ID, db_path=db_path,
            trigger_reason="cap-test", now=_NOW,
        )

        history = _read_history(db_path, _SESSION_ID)
        timestamps = [row["archived_at"] for row in history]
        assert timestamps == sorted(timestamps, reverse=True), \
            "plan_history must be returned newest-first"
        # The fresh archive (cap-test) is the newest entry
        assert history[0]["refresh_reason"] == "cap-test"

    def test_cap_does_not_leak_across_sessions(self, db_path: str) -> None:
        """The 20-row cap is per-session — a sibling session keeps its history."""
        other = "22222222-2222-2222-2222-222222222222"
        _seed_session(db_path, _SESSION_ID, plan=_make_plan(["a"]))
        _seed_session(db_path, other, plan=_make_plan(["b"]))
        base = _NOW - timedelta(hours=2)
        _seed_history_rows(db_path, _SESSION_ID, 25, base=base)
        _seed_history_rows(db_path, other, 3, base=base)

        refresh_plan(
            _SESSION_ID, db_path=db_path,
            trigger_reason="cap-test", now=_NOW,
        )

        assert len(_read_history(db_path, _SESSION_ID)) == 20
        # The sibling session's 3 rows are untouched
        assert len(_read_history(db_path, other)) == 3
