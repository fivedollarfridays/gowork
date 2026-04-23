"""Tests for SendGrid email integration (T12.2).

Covers:
- Success path with mock provider + engagement_events write
- Kill switch (FEATURE_EMAIL_SEND_ENABLED=false) no-op
- Pre-send bounce dedup (recent vs old)
- Retry with exponential backoff (attempts + time.sleep calls)
- Final failure path + engagement_events "email_send_failed" row
- Category tagging on SendGrid payload (parametric)
- Structured logging (INFO success / WARNING retry / ERROR final)
- Mock provider never touches the network
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core import feature_flags
from app.integrations.email import EmailSendResult, send_transactional
from app.integrations.email import mock_provider
from app.integrations.email import sendgrid_client


# -------------------- Fixtures --------------------


_BOUNCE_SENDGRID_EVENT = (
    "INSERT INTO sendgrid_events (event_type, email, message_id, reason, "
    "raw_payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)"
)
_SELECT_ENGAGEMENT = (
    "SELECT category, payload_json FROM engagement_events "
    "ORDER BY id ASC"
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Create a temporary sqlite DB with the minimal m002 schema.

    We only need ``engagement_events`` and ``sendgrid_events`` plus a stub
    ``sessions`` row so FKs (when enabled) do not bite.
    """
    path = tmp_path / "test_email.db"
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE sessions (id TEXT PRIMARY KEY, created_at TEXT);
            CREATE TABLE engagement_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                category TEXT NOT NULL,
                payload_json TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE sendgrid_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                email TEXT,
                message_id TEXT,
                reason TEXT,
                raw_payload_json TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            "INSERT INTO sessions (id, created_at) VALUES (?, ?)",
            ("sess-1", datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    return path


@pytest.fixture(autouse=True)
def _reset_feature_flags(monkeypatch):
    """Ensure FEATURE_EMAIL_SEND_ENABLED env defaults to on for each test."""
    monkeypatch.delenv("FEATURE_EMAIL_SEND_ENABLED", raising=False)
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    """Record time.sleep calls rather than actually sleeping."""
    calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    monkeypatch.setattr(sendgrid_client.time, "sleep", fake_sleep)
    return calls


@pytest.fixture
def use_mock_client(monkeypatch):
    """Install a canned-success mock SendGrid client."""
    client = mock_provider.MockSendGridClient()
    monkeypatch.setattr(sendgrid_client, "_build_client", lambda: client)
    return client


@pytest.fixture
def force_flag_true(monkeypatch):
    """Force FEATURE_EMAIL_SEND_ENABLED to always be true for a test."""
    monkeypatch.setenv("FEATURE_EMAIL_SEND_ENABLED", "true")


# -------------------- Helpers --------------------


def _engagement_rows(db_path: Path) -> list[tuple[str, dict]]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(_SELECT_ENGAGEMENT).fetchall()
    finally:
        conn.close()
    return [(r[0], json.loads(r[1]) if r[1] else {}) for r in rows]


def _seed_bounce(db_path: Path, email: str, age_days: int, reason: str = "hard") -> None:
    ts = (datetime.now(timezone.utc) - timedelta(days=age_days)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            _BOUNCE_SENDGRID_EVENT,
            ("bounce", email, "mid-old", reason, "{}", ts),
        )
        conn.commit()
    finally:
        conn.close()


# -------------------- Cycle 1: success path --------------------


def test_send_success_returns_success_result(
    db_path: Path, use_mock_client, force_flag_true
) -> None:
    result = send_transactional(
        to="user@example.com",
        subject="Hi",
        html="<p>hi</p>",
        text_fallback="hi",
        category="digest",
        session_id="sess-1",
        db_path=db_path,
    )
    assert isinstance(result, EmailSendResult)
    assert result.success is True
    assert result.message_id is not None
    assert result.attempt_count == 1
    assert result.skipped_reason is None
    rows = _engagement_rows(db_path)
    assert len(rows) == 1
    category, payload = rows[0]
    assert category == "email_sent"
    assert payload["to"] == "user@example.com"
    assert payload["category"] == "digest"
    assert payload["attempts"] == 1


# -------------------- Cycle 2: kill switch --------------------


def test_kill_switch_skips_send(
    db_path: Path, monkeypatch, use_mock_client
) -> None:
    monkeypatch.setenv("FEATURE_EMAIL_SEND_ENABLED", "false")
    result = send_transactional(
        to="user@example.com",
        subject="Hi",
        html="<p>hi</p>",
        text_fallback="hi",
        category="reminder",
        session_id="sess-1",
        db_path=db_path,
    )
    assert result.success is False
    assert result.skipped_reason == "kill_switch"
    assert result.attempt_count == 0
    assert result.message_id is None
    assert use_mock_client.calls == []  # no HTTP / send happened
    # Kill-switch does not write an engagement row (audit via log line only)
    assert _engagement_rows(db_path) == []


# -------------------- Cycle 3: bounce dedup --------------------


def test_recent_hard_bounce_skips_send(
    db_path: Path, use_mock_client, force_flag_true
) -> None:
    _seed_bounce(db_path, "user@example.com", age_days=2, reason="hard bounce")
    result = send_transactional(
        to="user@example.com",
        subject="Hi",
        html="<p>hi</p>",
        text_fallback="hi",
        category="digest",
        session_id="sess-1",
        db_path=db_path,
    )
    assert result.success is False
    assert result.skipped_reason == "recent_hard_bounce"
    assert result.attempt_count == 0
    assert use_mock_client.calls == []


def test_old_bounce_does_not_skip(
    db_path: Path, use_mock_client, force_flag_true
) -> None:
    _seed_bounce(db_path, "user@example.com", age_days=30, reason="hard bounce")
    result = send_transactional(
        to="user@example.com",
        subject="Hi",
        html="<p>hi</p>",
        text_fallback="hi",
        category="digest",
        session_id="sess-1",
        db_path=db_path,
    )
    assert result.success is True
    assert result.skipped_reason is None


# -------------------- Cycle 4: retry + failure paths --------------------


def test_retry_backoff_on_transient_failure(
    db_path: Path, monkeypatch, _no_real_sleep, force_flag_true
) -> None:
    flakey = mock_provider.FlakeyMockSendGridClient(fail_first_n=2)
    monkeypatch.setattr(sendgrid_client, "_build_client", lambda: flakey)
    result = send_transactional(
        to="user@example.com",
        subject="Hi",
        html="<p>hi</p>",
        text_fallback="hi",
        category="digest",
        session_id="sess-1",
        db_path=db_path,
    )
    assert result.success is True
    assert result.attempt_count == 3
    assert _no_real_sleep == [1, 2]  # backoff between attempts 1->2, 2->3


def test_final_failure_logs_engagement_event(
    db_path: Path, monkeypatch, _no_real_sleep, force_flag_true
) -> None:
    failing = mock_provider.FailingMockSendGridClient()
    monkeypatch.setattr(sendgrid_client, "_build_client", lambda: failing)
    result = send_transactional(
        to="user@example.com",
        subject="Hi",
        html="<p>hi</p>",
        text_fallback="hi",
        category="digest",
        session_id="sess-1",
        db_path=db_path,
    )
    assert result.success is False
    assert result.skipped_reason is None
    assert result.attempt_count == 3
    rows = _engagement_rows(db_path)
    assert len(rows) == 1
    category, payload = rows[0]
    assert category == "email_send_failed"
    assert payload["attempts"] == 3
    assert "error" in payload and payload["error"]


# -------------------- Cycle 5: categories + logging --------------------


@pytest.mark.parametrize(
    "category",
    [
        "digest",
        "reminder",
        "stall_alert",
        "appointment_confirmation",
        "appointment_reminder",
    ],
)
def test_category_parametric(
    db_path: Path, use_mock_client, force_flag_true, category
) -> None:
    result = send_transactional(
        to="user@example.com",
        subject="S",
        html="<p>x</p>",
        text_fallback="x",
        category=category,
        session_id="sess-1",
        db_path=db_path,
    )
    assert result.success is True
    sent_payload = use_mock_client.calls[-1]
    assert category in sent_payload["categories"]


def test_structured_logging_on_retries(
    db_path: Path, monkeypatch, caplog, _no_real_sleep, force_flag_true
) -> None:
    flakey = mock_provider.FlakeyMockSendGridClient(fail_first_n=2)
    monkeypatch.setattr(sendgrid_client, "_build_client", lambda: flakey)
    with caplog.at_level(logging.DEBUG, logger="app.integrations.email"):
        send_transactional(
            to="user@example.com",
            subject="Hi",
            html="<p>hi</p>",
            text_fallback="hi",
            category="digest",
            session_id="sess-1",
            db_path=db_path,
        )
    levels = [r.levelno for r in caplog.records if r.name.startswith("app.integrations.email")]
    assert logging.WARNING in levels  # at least one retry warning
    assert logging.INFO in levels     # final success info


def test_structured_logging_on_final_failure(
    db_path: Path, monkeypatch, caplog, _no_real_sleep, force_flag_true
) -> None:
    failing = mock_provider.FailingMockSendGridClient()
    monkeypatch.setattr(sendgrid_client, "_build_client", lambda: failing)
    with caplog.at_level(logging.DEBUG, logger="app.integrations.email"):
        send_transactional(
            to="user@example.com",
            subject="Hi",
            html="<p>hi</p>",
            text_fallback="hi",
            category="digest",
            session_id="sess-1",
            db_path=db_path,
        )
    levels = [r.levelno for r in caplog.records if r.name.startswith("app.integrations.email")]
    assert logging.ERROR in levels


# -------------------- Cycle 6: mock provider safety --------------------


def test_mock_provider_does_not_call_network() -> None:
    """MockSendGridClient.send must not import or invoke httpx/sendgrid."""
    client = mock_provider.MockSendGridClient()
    result = client.send({"to": "a@b.c", "subject": "s", "categories": ["digest"]})
    assert result["status_code"] == 202
    assert result["message_id"]
    # Record retained for assertions
    assert client.calls[-1]["to"] == "a@b.c"
