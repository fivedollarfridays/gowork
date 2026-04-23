"""Tests for engagement.cooldown — dedup state backed by reminder_cooldowns.

Covers check_cooldown (empty / recent / old / different-category),
record_send (persistence), get_cooldown_status (observability),
_apply_cooldown_filter (batch filter helper).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner

_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "cooldown.db")
    runner.apply_pending(path)
    _seed_session(path, "sid-1")
    _seed_session(path, "sid-2")
    return path


def _seed_session(db_path: str, session_id: str) -> None:
    """Insert a minimal session row so FK constraints pass."""
    now_iso = _NOW.isoformat()
    expires = (_NOW + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO sessions "
            "(id, created_at, barriers, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, now_iso, "[]", expires),
        )
        conn.commit()
    finally:
        conn.close()


def test_check_cooldown_empty_returns_true(db_path: str) -> None:
    """No prior rows → safe to send."""
    from app.modules.engagement.cooldown import check_cooldown

    assert check_cooldown(
        "sid-1", "stall_soft", db_path=db_path, now=_NOW,
    ) is True


def test_check_cooldown_recent_same_category_returns_false(db_path: str) -> None:
    """A row within the 24h window → must suppress."""
    from app.modules.engagement.cooldown import check_cooldown, record_send

    record_send("sid-1", "stall_soft", "soft", db_path=db_path, now=_NOW)
    later = _NOW + timedelta(hours=5)
    assert check_cooldown(
        "sid-1", "stall_soft", db_path=db_path, now=later,
    ) is False


def test_check_cooldown_old_same_category_returns_true(db_path: str) -> None:
    """A row older than 24h → safe to send again."""
    from app.modules.engagement.cooldown import check_cooldown, record_send

    record_send("sid-1", "stall_soft", "soft", db_path=db_path, now=_NOW)
    later = _NOW + timedelta(hours=25)
    assert check_cooldown(
        "sid-1", "stall_soft", db_path=db_path, now=later,
    ) is True


def test_check_cooldown_different_category_independent(db_path: str) -> None:
    """A SOFT send does not cool down the MEDIUM category."""
    from app.modules.engagement.cooldown import check_cooldown, record_send

    record_send("sid-1", "stall_soft", "soft", db_path=db_path, now=_NOW)
    assert check_cooldown(
        "sid-1", "stall_medium", db_path=db_path, now=_NOW,
    ) is True


def test_check_cooldown_different_session_independent(db_path: str) -> None:
    """A send for sid-1 does not cool down sid-2."""
    from app.modules.engagement.cooldown import check_cooldown, record_send

    record_send("sid-1", "stall_soft", "soft", db_path=db_path, now=_NOW)
    assert check_cooldown(
        "sid-2", "stall_soft", db_path=db_path, now=_NOW,
    ) is True


def test_record_send_inserts_row(db_path: str) -> None:
    """record_send writes exactly one reminder_cooldowns row."""
    from app.modules.engagement.cooldown import record_send

    record_send("sid-1", "stall_soft", "soft", db_path=db_path, now=_NOW)
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT session_id, category, last_sent_at, stall_level "
            "FROM reminder_cooldowns"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 1
    assert rows[0][0] == "sid-1"
    assert rows[0][1] == "stall_soft"
    assert rows[0][2] == _NOW.isoformat()


def test_get_cooldown_status_returns_all_categories(db_path: str) -> None:
    """get_cooldown_status surfaces last_sent_at + stall_level per category."""
    from app.modules.engagement.cooldown import get_cooldown_status, record_send

    record_send("sid-1", "stall_soft", "soft", db_path=db_path, now=_NOW)
    later = _NOW + timedelta(hours=1)
    record_send("sid-1", "digest", None, db_path=db_path, now=later)

    status = get_cooldown_status("sid-1", db_path=db_path)
    assert set(status.keys()) == {"stall_soft", "digest"}
    assert status["stall_soft"]["last_sent_at"] == _NOW.isoformat()
    assert status["stall_soft"]["stall_level"] == "soft"
    assert status["digest"]["last_sent_at"] == later.isoformat()


def test_apply_cooldown_filter_removes_cooled_sessions(db_path: str) -> None:
    """_apply_cooldown_filter drops items for (session, category) on cooldown."""
    from app.modules.engagement.cooldown import (
        _apply_cooldown_filter,
        record_send,
    )

    record_send("sid-1", "stall_soft", "soft", db_path=db_path, now=_NOW)
    candidates = [
        {"session_id": "sid-1", "category": "stall_soft"},
        {"session_id": "sid-2", "category": "stall_soft"},
    ]
    result = _apply_cooldown_filter(candidates, db_path=db_path, now=_NOW)
    assert len(result) == 1
    assert result[0]["session_id"] == "sid-2"
