"""Tests for engagement.reminder_engine — single send path for reminders + digests.

Critical behaviors:
- Dedup keyed on (session_id, stall_level) so a 3-barrier stall emits ONE SOFT
- SOFT→MEDIUM transition produces two emails (different categories)
- reminders_auto_disabled engagement_events row suppresses future sends
- EMAIL_SEND_ENABLED kill switch suppresses send
- Unsubscribe link present in body
- HTML-escape for worker-supplied fields
- Nightly orchestrator routes digest through reminder_engine.send_digest
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from app.core import feature_flags
from app.core.migrations import runner
from app.modules.common.temporal_types import StallLevel

_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)


@dataclass
class _FakeResult:
    """Stand-in for app.integrations.email.core.EmailSendResult."""

    success: bool
    message_id: str | None = "mid-stub"
    attempt_count: int = 1
    skipped_reason: str | None = None


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _reset_feature_flags() -> None:
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


@pytest.fixture(autouse=True)
def _unsubscribe_secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reminder + digest paths now sign real unsubscribe tokens."""
    monkeypatch.setenv(
        "UNSUBSCRIBE_TOKEN_SECRET",
        "reminder-engine-test-unsub-secret-0123456789ab",
    )
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "reminders.db")
    runner.apply_pending(path)
    return path


def _seed_session(
    db_path: str,
    session_id: str,
    *,
    email: str = "worker@example.com",
    first_name: str = "Jordan",
    barriers: list[str] | None = None,
) -> None:
    profile = {"email": email, "first_name": first_name}
    now_iso = _NOW.isoformat()
    expires = (_NOW + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions "
            "(id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                session_id,
                now_iso,
                json.dumps(barriers or []),
                json.dumps(profile),
                expires,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_auto_disabled(db_path: str, session_id: str) -> None:
    """Insert an engagement_events row flagging reminders as auto-disabled."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO engagement_events "
            "(session_id, category, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                session_id,
                "reminders_auto_disabled",
                json.dumps({"reason": "hard_bounce"}),
                _NOW.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _count_cooldown_rows(db_path: str, category: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM reminder_cooldowns WHERE category = ?",
            (category,),
        ).fetchone()
    finally:
        conn.close()
    return row[0]


def _install_sendgrid_spy(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Spy on reminder_engine.send_transactional. Returns the call log."""
    calls: list[dict] = []

    def _fake_send(
        to: str,
        subject: str,
        html: str,
        text_fallback: str,
        category: str,
        *,
        session_id: str | None = None,
        db_path: Any = None,
    ):
        calls.append(
            {
                "to": to,
                "subject": subject,
                "html": html,
                "text": text_fallback,
                "category": category,
                "session_id": session_id,
            }
        )
        return _FakeResult(success=True)

    import app.modules.engagement.reminder_engine as re_mod

    monkeypatch.setattr(re_mod, "send_transactional", _fake_send)
    return calls


# -------------------- Reminder tests --------------------


def test_single_reminder_sends_and_records_cooldown(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_session(db_path, "sid-1")
    calls = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.reminder_engine import send_reminder

    result = send_reminder(
        "sid-1", StallLevel.SOFT, db_path=db_path, now=_NOW,
    )
    assert result.success is True
    assert result.skipped_reason is None
    assert result.category == "stall_soft"
    assert len(calls) == 1
    assert _count_cooldown_rows(db_path, "stall_soft") == 1


def test_three_stalled_barriers_produce_one_soft_email(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Critical dedup case from the backlog: 3 barriers → exactly 1 SOFT email."""
    _seed_session(db_path, "sid-1", barriers=["b1", "b2", "b3"])
    calls = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.reminder_engine import send_reminder

    for _ in range(3):
        send_reminder("sid-1", StallLevel.SOFT, db_path=db_path, now=_NOW)

    # First call sends, next two hit cooldown
    assert len(calls) == 1
    assert _count_cooldown_rows(db_path, "stall_soft") == 1


def test_soft_then_medium_transition_produces_two_emails(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Different stall levels use different categories → independent cooldown."""
    _seed_session(db_path, "sid-1")
    calls = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.reminder_engine import send_reminder

    send_reminder("sid-1", StallLevel.SOFT, db_path=db_path, now=_NOW)
    # MEDIUM the next day — independent category, must send.
    later = _NOW + timedelta(hours=25)
    send_reminder("sid-1", StallLevel.MEDIUM, db_path=db_path, now=later)

    assert len(calls) == 2
    assert calls[0]["category"] == "stall_soft"
    assert calls[1]["category"] == "stall_medium"


def test_reminder_skipped_when_reminders_auto_disabled(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_session(db_path, "sid-1")
    _seed_auto_disabled(db_path, "sid-1")
    calls = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.reminder_engine import send_reminder

    result = send_reminder(
        "sid-1", StallLevel.SOFT, db_path=db_path, now=_NOW,
    )
    assert result.success is False
    assert result.skipped_reason == "reminders_disabled"
    assert calls == []
    assert _count_cooldown_rows(db_path, "stall_soft") == 0


def test_reminder_skipped_on_kill_switch(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_session(db_path, "sid-1")
    calls = _install_sendgrid_spy(monkeypatch)
    monkeypatch.setenv("FEATURE_EMAIL_SEND_ENABLED", "false")

    from app.modules.engagement.reminder_engine import send_reminder

    result = send_reminder(
        "sid-1", StallLevel.SOFT, db_path=db_path, now=_NOW,
    )
    assert result.success is False
    assert result.skipped_reason == "kill_switch"
    assert calls == []
    assert _count_cooldown_rows(db_path, "stall_soft") == 0


def test_unsubscribe_link_in_body(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CAN-SPAM: every reminder HTML body contains an unsubscribe URL."""
    _seed_session(db_path, "sid-1")
    calls = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.reminder_engine import send_reminder

    send_reminder("sid-1", StallLevel.SOFT, db_path=db_path, now=_NOW)
    assert "/api/engagement/unsubscribe?token=" in calls[0]["html"]
    assert "/api/engagement/unsubscribe?token=" in calls[0]["text"]


def test_html_escape_in_reminder_body(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Worker-supplied fields (first_name with `<`) are HTML-escaped."""
    _seed_session(db_path, "sid-1", first_name="<Jordan>")
    calls = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.reminder_engine import send_reminder

    send_reminder("sid-1", StallLevel.SOFT, db_path=db_path, now=_NOW)
    body = calls[0]["html"]
    assert "&lt;Jordan&gt;" in body
    assert "<Jordan>" not in body


def test_reminder_skipped_when_session_missing_email(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A session with no profile email is skipped cleanly."""
    now_iso = _NOW.isoformat()
    expires = (_NOW + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions "
            "(id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "sid-no-email",
                now_iso,
                "[]",
                json.dumps({"first_name": "Worker"}),
                expires,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    calls = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.reminder_engine import send_reminder

    result = send_reminder(
        "sid-no-email", StallLevel.SOFT, db_path=db_path, now=_NOW,
    )
    assert result.success is False
    assert result.skipped_reason == "no_email"
    assert calls == []


def test_send_digest_records_cooldown(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Digest path also writes to reminder_cooldowns with category='digest'."""
    _seed_session(db_path, "sid-1")
    calls = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.reminder_engine import send_digest

    result = send_digest(
        "sid-1",
        "worker@example.com",
        "[MontGoWork] Your daily digest",
        "<p>body</p>",
        "body",
        db_path=db_path,
        now=_NOW,
    )
    assert result.success is True
    assert result.category == "digest"
    assert len(calls) == 1
    assert calls[0]["category"] == "digest"
    assert _count_cooldown_rows(db_path, "digest") == 1


def test_send_digest_respects_cooldown(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_session(db_path, "sid-1")
    calls = _install_sendgrid_spy(monkeypatch)

    from app.modules.engagement.reminder_engine import send_digest

    send_digest(
        "sid-1", "worker@example.com", "subj", "<p>x</p>", "x",
        db_path=db_path, now=_NOW,
    )
    result = send_digest(
        "sid-1", "worker@example.com", "subj", "<p>x</p>", "x",
        db_path=db_path, now=_NOW + timedelta(hours=1),
    )
    assert len(calls) == 1
    assert result.success is False
    assert result.skipped_reason == "cooldown"


@pytest.mark.anyio
async def test_nightly_orchestrator_uses_reminder_engine(
    db_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T12.25 orchestrator routes the digest through reminder_engine.send_digest."""
    _seed_session(db_path, "mty-1")
    # Tag with city via outcomes_records so orchestrator picks it up.
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                "mty-1",
                "city_tag",
                json.dumps({"city": "montgomery"}),
                _NOW.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    captured: list[dict] = []

    def _spy_send_digest(
        session_id, to_email, subject, html, text, *, db_path, now=None,
    ):
        captured.append({"session_id": session_id, "to_email": to_email})
        return _FakeResult(success=True)

    import scripts.nightly_digest as nd

    monkeypatch.setattr(nd, "send_digest", _spy_send_digest)

    # Stub compose + retro (copied minimal stubs from test_nightly_digest.py)
    from app.modules.engagement.digest_composer import DigestResult

    def _fake_compose(session_id, for_date, *, db_path, city=None, now=None):
        return DigestResult(
            subject=f"digest-{session_id}",
            html="<p>body</p>",
            text="body",
            section_counts={"yesterday": 0, "today": 0, "week": 0, "stall": 0},
        )

    monkeypatch.setattr(nd, "compose_digest", _fake_compose)

    from datetime import date as _date

    from app.modules.plan.daily_progress import RetroResult

    def _fake_retro(session_id, for_date, *, db_path):
        return RetroResult(
            session_id=session_id,
            for_date=for_date if isinstance(for_date, _date) else _date.today(),
            actions=[],
            completion_ratio=0.0,
            summary="stub",
        )

    monkeypatch.setattr(nd, "run_nightly_retro", _fake_retro)

    from scripts.nightly_digest import run_nightly_digest

    results = await run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    )

    assert len(captured) == 1
    assert captured[0]["session_id"] == "mty-1"
    assert captured[0]["to_email"] == "worker@example.com"
    assert results[0].emails_sent == 1
