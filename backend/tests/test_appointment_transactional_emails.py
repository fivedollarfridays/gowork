"""Tests for appointment transactional emails (T12.10a).

Covers:
- ``build_manage_url`` produces a signed URL with action + token (T12.10b).
- ``send_confirmation`` invokes SendGrid with category ``appointment_confirmation``.
- Placeholder appointments (``starts_at is None``) skip with the right reason.
- Confirmation email HTML contains cancel + reschedule signed manage URLs.
- Worker first name is HTML-escaped when rendered.
- ``scan_and_send_reminders`` locates 24h + 1h window appointments.
- Second scan dedupes via ``cooldown.check_cooldown`` (no duplicate sends).
- Cancelled appointments are skipped by the scan.
- The scheduler's ``appointment_reminders`` job invokes the scan function.
- ``register_transactional_email_listener`` is idempotent.
- Time rendered via ``format_city_local`` appears in the email body.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core import events
from app.core.migrations import runner
from app.integrations.email.core import EmailSendResult
from app.modules.appointments import persistence, transactional_emails
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import (
    AppointmentStatus,
    AppointmentType,
)

_SESSION = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SECRET = "current-secret-for-tests-only-0123456789"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    # Also reset the listener registration sentinel between tests.
    transactional_emails._REGISTRATION_SENTINEL.clear()
    yield
    events.clear_all_subscribers()
    transactional_emails._REGISTRATION_SENTINEL.clear()


@pytest.fixture(autouse=True)
def _secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Token signing secret and APP_HOST for manage-URL construction."""
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", _SECRET)
    monkeypatch.delenv("APPOINTMENT_TOKEN_SECRET_OLD", raising=False)
    monkeypatch.setenv("APP_HOST", "https://app.example.com")


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "txn_email.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION, first_name="Alice", email="alice@example.com")
    return path


def _seed_session(
    path: str, session_id: str, *, first_name: str, email: str,
) -> None:
    """Insert a sessions row with a profile JSON carrying name + email."""
    import json
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        profile = json.dumps({"first_name": first_name, "email": email})
        conn.execute(
            "INSERT INTO sessions "
            "(id, created_at, barriers, expires_at, profile) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, now, "[]", now, profile),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def captured_sends(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Monkeypatch ``send_transactional`` on the dispatch layer."""
    from app.modules.appointments import _email_dispatch

    calls: list[dict] = []

    def _fake_send(
        to: str,
        subject: str,
        html: str,
        text_fallback: str,
        category: str,
        *,
        session_id: str | None = None,
        db_path: str | Path | None = None,
    ) -> EmailSendResult:
        calls.append({
            "to": to, "subject": subject, "html": html,
            "text": text_fallback, "category": category,
            "session_id": session_id,
        })
        return EmailSendResult(
            success=True, message_id="mid-test",
            attempt_count=1, skipped_reason=None,
        )

    monkeypatch.setattr(
        _email_dispatch, "send_transactional", _fake_send,
    )
    return calls


def _make_appointment(
    *,
    db_path: str,
    session_id: str = _SESSION,
    starts_offset_h: float = 24.0,
    duration_min: int = 60,
    status: AppointmentStatus = AppointmentStatus.SCHEDULED,
    title: str = "DMV visit",
) -> Appointment:
    """Persist an appointment and return the stored Appointment."""
    starts = datetime.now(timezone.utc) + timedelta(hours=starts_offset_h)
    appt = Appointment(
        session_id=session_id,
        type=AppointmentType.DMV,
        title=title,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=duration_min),
        location_name="DMV Office",
        status=status,
    )
    return persistence.insert(appt, db_path=db_path)


# -------------------- Cycle 1: build_manage_url --------------------


def test_build_manage_url_contains_token_and_action(db_path: str) -> None:
    """URL has https scheme, host, action param, and a signed token payload."""
    # Seed one appointment so the id exists.
    stored = _make_appointment(db_path=db_path)
    url = transactional_emails.build_manage_url(
        stored.id, "cancel", app_host="https://app.example.com",
    )
    assert url.startswith("https://app.example.com/api/appointments/manage?")
    assert "action=cancel" in url
    assert "token=" in url
    # Signed tokens are <encoded>.<sig>, so a '.' should be in the token param.
    token_part = url.split("token=", 1)[1].split("&", 1)[0]
    assert "." in token_part


def test_build_manage_url_uses_tokens_sign(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assert we delegate to T12.10b tokens.sign — not a local stub."""
    from app.modules.appointments import _email_rendering, tokens

    stored = _make_appointment(db_path=db_path)
    called: list[tuple[int, object]] = []
    real_sign = tokens.sign

    def spy_sign(appointment_id, action, **kwargs):
        called.append((appointment_id, action))
        return real_sign(appointment_id, action, **kwargs)

    monkeypatch.setattr(_email_rendering, "tokens_sign", spy_sign)
    transactional_emails.build_manage_url(
        stored.id, "reschedule", app_host="https://app.example.com",
    )
    assert called, "tokens.sign must be invoked via build_manage_url"
    assert called[0][0] == stored.id


# -------------------- Cycle 2: send_confirmation happy path --------------------


def test_send_confirmation_invokes_sendgrid_with_category(
    db_path: str, captured_sends: list[dict],
) -> None:
    """Happy path: a scheduled appointment produces one send with right category."""
    stored = _make_appointment(db_path=db_path)
    result = transactional_emails.send_confirmation(stored, db_path=db_path)
    assert result.success is True
    assert result.category == "appointment_confirmation"
    assert result.skipped_reason is None
    assert len(captured_sends) == 1
    sent = captured_sends[0]
    assert sent["to"] == "alice@example.com"
    assert sent["category"] == "appointment_confirmation"
    assert sent["session_id"] == _SESSION


# -------------------- Cycle 3: placeholder skip --------------------


def test_send_confirmation_skipped_for_placeholder_appointment(
    db_path: str, captured_sends: list[dict],
) -> None:
    """pathway_auto placeholder with starts_at=None is skipped cleanly."""
    placeholder = Appointment(
        session_id=_SESSION,
        type=AppointmentType.DMV,
        title="DMV (TBD)",
        starts_at=None,
        status=AppointmentStatus.SCHEDULED,
        source="pathway_auto",
    )
    stored = persistence.insert(placeholder, db_path=db_path)
    result = transactional_emails.send_confirmation(stored, db_path=db_path)
    assert result.success is False
    assert result.skipped_reason == "missing_starts_at"
    assert captured_sends == []


# -------------------- Cycle 4: manage URL injected into email --------------------


def test_confirmation_email_includes_cancel_and_reschedule_urls(
    db_path: str, captured_sends: list[dict],
) -> None:
    """HTML body contains the signed manage-URL for both cancel + reschedule."""
    stored = _make_appointment(db_path=db_path)
    transactional_emails.send_confirmation(stored, db_path=db_path)
    body = captured_sends[0]["html"]
    assert "action=cancel" in body
    assert "action=reschedule" in body
    # The signed-token path has the signature '.' delimiter.
    assert body.count("token=") >= 2


# -------------------- Cycle 5: HTML escaping --------------------


def test_worker_first_name_html_escaped(
    db_path: str, captured_sends: list[dict],
) -> None:
    """First name with HTML metacharacters is escaped, not rendered."""
    # Re-seed with a dangerous first_name.
    session_id = "ffffffff-0000-1111-2222-333333333333"
    _seed_session(
        db_path, session_id,
        first_name="Alice <script>",
        email="alice@example.com",
    )
    stored = _make_appointment(db_path=db_path, session_id=session_id)
    transactional_emails.send_confirmation(stored, db_path=db_path)
    body = captured_sends[0]["html"]
    assert "&lt;script&gt;" in body
    assert "<script>" not in body


# -------------------- Cycle 6: scan finds 24h + 1h windows --------------------


def test_scan_finds_appointments_in_24h_and_1h_windows(
    db_path: str, captured_sends: list[dict],
) -> None:
    """Seed 4 appts: +24h, +23.5h, +1h, +10h. Scan returns 24h + 1h hits only."""
    now = datetime.now(timezone.utc)
    _make_appointment(db_path=db_path, starts_offset_h=24.0, title="at 24h")
    _make_appointment(db_path=db_path, starts_offset_h=23.5, title="at 23.5h")
    _make_appointment(db_path=db_path, starts_offset_h=1.0, title="at 1h")
    _make_appointment(db_path=db_path, starts_offset_h=10.0, title="at 10h")
    results = transactional_emails.scan_and_send_reminders(
        db_path=db_path, now=now,
    )
    successes = [r for r in results if r.success]
    categories = sorted(r.category for r in successes)
    assert categories == sorted([
        "appointment_reminder_24h", "appointment_reminder_1h",
    ])
    # Two sends only (24h + 1h).
    assert len(captured_sends) == 2


# -------------------- Cycle 7: dedupe via cooldown --------------------


def test_scan_dedupes_second_run_via_cooldown(
    db_path: str, captured_sends: list[dict],
) -> None:
    """Running scan twice in a row only sends one email per appointment."""
    now = datetime.now(timezone.utc)
    _make_appointment(db_path=db_path, starts_offset_h=1.0, title="soon")
    r1 = transactional_emails.scan_and_send_reminders(
        db_path=db_path, now=now,
    )
    r2 = transactional_emails.scan_and_send_reminders(
        db_path=db_path, now=now,
    )
    assert len([r for r in r1 if r.success]) == 1
    assert all(r.skipped_reason == "cooldown" for r in r2 if not r.success)
    # One total send captured (second run is deduped).
    assert len(captured_sends) == 1


# -------------------- Cycle 8: cancelled appointments skipped --------------------


def test_scan_skips_cancelled_appointments(
    db_path: str, captured_sends: list[dict],
) -> None:
    """Cancelled status in the 1h window does not produce a send."""
    now = datetime.now(timezone.utc)
    _make_appointment(
        db_path=db_path, starts_offset_h=1.0,
        status=AppointmentStatus.CANCELLED, title="cancelled soon",
    )
    results = transactional_emails.scan_and_send_reminders(
        db_path=db_path, now=now,
    )
    assert [r for r in results if r.success] == []
    assert captured_sends == []


# -------------------- Cycle 9: scheduler job invokes handler --------------------


def test_scheduler_job_invokes_scan(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When appointment_reminders job fires, scan_and_send_reminders runs."""
    from app.core import scheduler as sched_mod

    called: list[dict] = []

    def fake_scan(**kwargs):
        called.append(kwargs)
        return []

    monkeypatch.setattr(sched_mod, "_TESTING", True)
    sched_mod._reset_for_tests()
    # Patch the resolver used by the handler to point at our tmp DB.
    monkeypatch.setattr(
        "app.routes._appointments_helpers.resolve_db_path",
        lambda: db_path,
    )
    monkeypatch.setattr(
        transactional_emails, "scan_and_send_reminders", fake_scan,
    )
    try:
        sched_mod.start_scheduler()
        sched = sched_mod.get_scheduler()
        job = sched.get_job("appointment_reminders")
        assert job is not None
        # The job.func is the async handler; run it synchronously.
        import asyncio
        asyncio.run(job.func())
    finally:
        sched_mod._reset_for_tests()
    assert called, "scan_and_send_reminders must be invoked from the job"


# -------------------- Cycle 10: listener idempotent --------------------


def test_register_listener_is_idempotent(
    db_path: str, captured_sends: list[dict],
) -> None:
    """Two register calls -> exactly one handler invocation per event."""
    transactional_emails.register_transactional_email_listener(db_path)
    transactional_emails.register_transactional_email_listener(db_path)
    stored = _make_appointment(db_path=db_path)
    # Emit manually (scheduler.create would also do this).
    events.emit("appointment.created", stored.model_dump(mode="json"))
    assert len(captured_sends) == 1


# -------------------- Cycle 11: time rendered in city-local --------------------


def test_time_rendered_in_city_local(
    db_path: str, captured_sends: list[dict],
) -> None:
    """A UTC time appears in the email formatted via format_city_local."""
    # 2026-04-10 17:00 UTC -> Friday April 10 at 12:00pm CT (Montgomery).
    fixed_utc = datetime(2026, 4, 10, 17, 0, tzinfo=timezone.utc)
    appt = Appointment(
        session_id=_SESSION,
        type=AppointmentType.DMV,
        title="DMV visit",
        starts_at=fixed_utc,
        ends_at=fixed_utc + timedelta(hours=1),
        location_name="DMV Office",
        status=AppointmentStatus.SCHEDULED,
    )
    stored = persistence.insert(appt, db_path=db_path)
    transactional_emails.send_confirmation(stored, db_path=db_path)
    body = captured_sends[0]["html"]
    # The format_city_local output for (2026-04-10 17:00 UTC, montgomery) is:
    # 'Friday April 10 at 12:00pm CT'
    assert "Friday April 10" in body
    assert "12:00pm CT" in body
