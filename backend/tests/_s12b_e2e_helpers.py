"""Helpers for the S12b end-to-end integration tests (T12.32b).

Extracted from ``test_s12b_worker_companion_e2e.py`` to keep that
module under the arch 600-line / 30-import / 50-line-per-function
limits. Pure test utilities — seeding, SendGrid spies, FastAPI client
builders, and PDF mocks.

The S12b scope spans many modules (resume/cover letter, PDF, signed
manage-links, reminder engine, plan refresher, appointment reconcile,
compliance export/delete, advisor inbox, retention). Each helper here
is a narrow single-purpose utility; tests compose them.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)


# -------------------- Constants exposed to tests --------------------

SESSION_MTG = "11111111-aaaa-4bbb-8ccc-111111111111"
SESSION_FTW = "22222222-aaaa-4bbb-8ccc-222222222222"
TOKEN_MTG = "tok-mtg-s12b-aaaaaaaaaaaaaaaaaaaa"
TOKEN_FTW = "tok-ftw-s12b-bbbbbbbbbbbbbbbbbbbb"

APPT_TOKEN_SECRET = "s12b-appt-secret-current-abcdef0123456789"
APPT_TOKEN_SECRET_OLD = "s12b-appt-secret-old-0123456789abcdef0"
COMPLIANCE_SECRET = "s12b-compliance-secret-fedcba9876543210"


# -------------------- Session seeding --------------------


def _build_profile(
    email: str, first_name: str, extras: dict[str, Any] | None,
) -> dict[str, Any]:
    profile: dict[str, Any] = {"email": email, "first_name": first_name}
    if extras:
        profile.update(extras)
    return profile


def _insert_session_row(
    conn: sqlite3.Connection, session_id: str, *,
    now_iso: str, exp_iso: str, barriers: list[str],
    profile: dict[str, Any], demo: bool,
    plan: dict[str, Any] | None, action_checklist: dict[str, Any] | None,
) -> None:
    conn.execute(
        "INSERT INTO sessions (id, created_at, barriers, profile, "
        "expires_at, plan, action_checklist, demo) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            session_id, now_iso, json.dumps(barriers),
            json.dumps(profile), exp_iso,
            json.dumps(plan or {}) if plan is not None else None,
            json.dumps(action_checklist or {}) if action_checklist else None,
            1 if demo else 0,
        ),
    )


def seed_session(
    db_path: str, session_id: str, token: str, *,
    city: str,
    barriers: list[str] | None = None,
    email: str = "worker@example.com",
    first_name: str = "Jordan",
    demo: bool = False,
    profile_extras: dict[str, Any] | None = None,
    expires_at: datetime | None = None,
    action_checklist: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
) -> None:
    """Seed sessions + feedback_tokens + a city-tag outcome row (city-tag at -200d)."""
    now_iso = _NOW.isoformat()
    exp_iso = (expires_at or (_NOW + timedelta(days=30))).isoformat()
    profile = _build_profile(email, first_name, profile_extras)
    conn = sqlite3.connect(db_path)
    try:
        _insert_session_row(
            conn, session_id, now_iso=now_iso, exp_iso=exp_iso,
            barriers=barriers or [], profile=profile, demo=demo,
            plan=plan, action_checklist=action_checklist,
        )
        conn.execute(
            "INSERT INTO feedback_tokens "
            "(token, session_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, session_id, now_iso, exp_iso),
        )
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                session_id, "city_tag", json.dumps({"city": city}),
                (_NOW - timedelta(days=200)).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def insert_recent_city_outcome(
    db_path: str, session_id: str, city: str, *, days_ago: int,
) -> None:
    """Insert a fresh outcomes_records row with a city payload.

    Used to give a session a RECENT (<90d) progress signal so the
    stall detector / advisor repository treats it as city-tagged.
    """
    ts = (_NOW - timedelta(days=days_ago)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                session_id, "plan_followed",
                json.dumps({"city": city}), ts,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def insert_advisor_token(
    db_path: str, plaintext: str, advisor_id: str, city: str,
) -> None:
    """Insert a live advisor_tokens row."""
    token_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO advisor_tokens "
            "(token_hash, advisor_id, city, issued_at, revoked_at, expires_at) "
            "VALUES (?, ?, ?, ?, NULL, NULL)",
            (token_hash, advisor_id, city, _NOW.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def insert_job_application(
    db_path: str, session_id: str, *,
    company: str = "Acme", role: str = "Barista",
) -> None:
    """Insert a minimal job_applications row for k-anonymity seeding."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO job_applications "
            "(session_id, match_source, match_url, company, role, status, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session_id, "indeed", "https://example.com/j/1",
                company, role, "applied", _NOW.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# -------------------- SendGrid spies --------------------


def install_sendgrid_spy(
    monkeypatch: pytest.MonkeyPatch, *, modules: list[str] | None = None,
) -> list[dict]:
    """Patch ``send_transactional`` on every module that imports it.

    The reminder_engine and appointment _email_dispatch both bind the
    callable at import time, so tests need to monkey-patch each binding
    to route all sends through one spy.
    """
    from app.integrations.email.core import EmailSendResult

    calls: list[dict] = []

    def _fake_send(
        to: str, subject: str, html: str, text_fallback: str,
        category: str,
        *, session_id: str | None = None, db_path: Any = None,
    ):
        calls.append({
            "to": to, "subject": subject, "html": html,
            "text": text_fallback, "category": category,
            "session_id": session_id,
        })
        return EmailSendResult(
            success=True, message_id=f"mid-{len(calls)}",
            attempt_count=1, skipped_reason=None,
        )

    target_modules = modules or [
        "app.modules.engagement.reminder_engine",
        "app.modules.appointments._email_dispatch",
    ]
    import importlib
    for mod_path in target_modules:
        mod = importlib.import_module(mod_path)
        if hasattr(mod, "send_transactional"):
            monkeypatch.setattr(mod, "send_transactional", _fake_send)
    return calls


# -------------------- FastAPI clients --------------------


def build_manage_client(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Mount the appointments_manage router only."""
    from app.routes import appointments_manage
    monkeypatch.setattr(
        appointments_manage, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(appointments_manage.router)
    return TestClient(app)


def build_compliance_client(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Mount the compliance router only."""
    from app.routes import compliance
    monkeypatch.setattr(compliance, "_resolve_db_path", lambda: db_path)
    app = FastAPI()
    app.include_router(compliance.router)
    return TestClient(app)


def build_advisor_client(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """Mount the advisor_inbox router only."""
    from app.routes import advisor_inbox
    monkeypatch.setattr(advisor_inbox, "_resolve_db_path", lambda: db_path)
    app = FastAPI()
    app.include_router(advisor_inbox.router)
    return TestClient(app)


# -------------------- Profile builders for resume / cover letter --------------------


def profile_with_free_text(
    *, name: str = "Jordan Rivers", summary: str = "Reliable worker.",
    notes: str | None = None,
    cleared_barriers: list[str] | None = None,
    email: str = "worker@example.com",
    first_name: str = "Jordan",
) -> dict[str, Any]:
    """Compose a session.profile dict for resume / cover-letter tests."""
    profile: dict[str, Any] = {
        "email": email, "first_name": first_name,
        "name": name, "summary": summary,
        "contact": "100 Main St\n" + email,
        "skills": ["punctual", "team player"],
        "work_history": [
            {
                "title": "Line Cook", "employer": "Diner",
                "dates": "2023-2024",
                "description": "Prepped and plated orders.",
            },
        ],
    }
    if notes is not None:
        profile["notes"] = notes
    if cleared_barriers:
        profile["cleared_barriers"] = cleared_barriers
    return profile


def update_profile(
    db_path: str, session_id: str, profile: dict[str, Any],
) -> None:
    """Overwrite sessions.profile for an existing row."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE sessions SET profile = ? WHERE id = ?",
            (json.dumps(profile), session_id),
        )
        conn.commit()
    finally:
        conn.close()


# -------------------- Appointment creation helpers --------------------


def create_scheduled_appointment(
    db_path: str, session_id: str, *,
    starts_offset_h: float, duration_min: int = 60,
    title: str = "DMV visit", location: str = "DMV office",
    barrier_link: str = "dmv_license",
) -> Any:
    """Insert a SCHEDULED appointment returning the stored Appointment.

    Bypasses the event bus — use ``scheduler.create`` directly when
    event emission matters for the test.
    """
    from app.modules.appointments import persistence
    from app.modules.appointments.types import Appointment
    from app.modules.common.temporal_types import (
        AppointmentStatus, AppointmentType,
    )
    starts = _NOW + timedelta(hours=starts_offset_h)
    appt = Appointment(
        session_id=session_id, type=AppointmentType.DMV,
        title=title,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=duration_min),
        location_name=location,
        barrier_link=barrier_link,
        status=AppointmentStatus.SCHEDULED,
    )
    return persistence.insert(appt, db_path=db_path)


def count_rows(db_path: str, table: str, where: str = "1=1",
                 params: tuple = ()) -> int:
    """Quick row-count helper used by assertions."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {where}", params,
        ).fetchone()
    finally:
        conn.close()
    return int(row[0])


def fetch_one(
    db_path: str, sql: str, params: tuple = (),
) -> tuple | None:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


def insert_record_profile(db_path: str, session_id: str) -> None:
    """Insert a minimal record_profiles row used by selective-delete tests."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO record_profiles (session_id, record_types, "
            "charge_categories, years_since_conviction, completed_sentence) "
            "VALUES (?, '[]', '[]', 5, 1)",
            (session_id,),
        )
        conn.commit()
    finally:
        conn.close()


def archive_n_plans(
    db_path: str, session_id: str, count: int, *, base_now: datetime,
) -> None:
    """Archive ``count`` plans for the session — used to test the 20-row cap."""
    from app.modules.plan import _plan_refresher_db
    for i in range(count):
        _plan_refresher_db.archive_plan(
            session_id, {"n": i}, db_path=db_path,
            archived_at=base_now + timedelta(seconds=i),
            refresh_reason="test", triggering_event=None,
        )


# -------------------- Test-driver shortcuts --------------------


def seed_three_cities(db_path: str) -> str:
    """Seed mtg + ftw + a montgomery demo session; return demo session id."""
    seed_session(db_path, SESSION_MTG, TOKEN_MTG, city="montgomery")
    insert_recent_city_outcome(db_path, SESSION_MTG, "montgomery", days_ago=10)
    seed_session(db_path, SESSION_FTW, TOKEN_FTW, city="fort-worth")
    insert_recent_city_outcome(db_path, SESSION_FTW, "fort-worth", days_ago=10)
    demo_sid = "33333333-aaaa-4bbb-8ccc-333333333333"
    seed_session(
        db_path, demo_sid, "tok-demo-cccccccccccccc",
        city="montgomery", demo=True,
    )
    insert_recent_city_outcome(db_path, demo_sid, "montgomery", days_ago=10)
    return demo_sid


def sign_token_with_secret(
    appointment_id: int, secret: str,
    monkeypatch: pytest.MonkeyPatch,
) -> str:
    """Sign an appointment VIEW token with an arbitrary current secret."""
    from app.modules.appointments import tokens as appt_tokens
    monkeypatch.setenv("APPOINTMENT_TOKEN_SECRET", secret)
    monkeypatch.delenv("APPOINTMENT_TOKEN_SECRET_OLD", raising=False)
    return appt_tokens.sign(appointment_id, appt_tokens.TokenAction.VIEW)


def run_concurrent_token_verify(
    token: str, db_path: str,
) -> dict[str, int]:
    """Two threads race to verify the same token; return win/used counts."""
    import threading as _threading
    from app.modules.appointments import tokens as appt_tokens
    results: dict[str, int] = {"ok": 0, "used": 0, "other": 0}
    barrier = _threading.Barrier(2)
    lock = _threading.Lock()

    def _worker() -> None:
        barrier.wait()
        try:
            appt_tokens.verify(
                token, appt_tokens.TokenAction.VIEW, db_path=db_path,
            )
            bucket = "ok"
        except appt_tokens.TokenAlreadyUsed:
            bucket = "used"
        except appt_tokens.TokenError:
            bucket = "other"
        with lock:
            results[bucket] += 1

    threads = [_threading.Thread(target=_worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def issue_uniform_401_probes(client) -> list:
    """GET /manage three times with distinct failure modes; return responses."""
    from app.modules.appointments import tokens as appt_tokens
    long_ago = datetime(2000, 1, 1, tzinfo=timezone.utc)
    expired = appt_tokens.sign(
        1, appt_tokens.TokenAction.VIEW,
        expires_in_sec=1, now=long_ago,
    )
    unknown = appt_tokens.sign(99999, appt_tokens.TokenAction.VIEW)
    out = []
    for token in ("not-a-real-token", expired, unknown):
        out.append(client.get(
            "/api/appointments/manage",
            params={"token": token, "action": "view"},
        ))
    return out


__all__ = [
    "APPT_TOKEN_SECRET",
    "APPT_TOKEN_SECRET_OLD",
    "COMPLIANCE_SECRET",
    "SESSION_FTW",
    "SESSION_MTG",
    "TOKEN_FTW",
    "TOKEN_MTG",
    "_NOW",
    "archive_n_plans",
    "build_advisor_client",
    "build_compliance_client",
    "build_manage_client",
    "count_rows",
    "create_scheduled_appointment",
    "fetch_one",
    "insert_advisor_token",
    "insert_job_application",
    "insert_recent_city_outcome",
    "insert_record_profile",
    "install_sendgrid_spy",
    "issue_uniform_401_probes",
    "profile_with_free_text",
    "run_concurrent_token_verify",
    "seed_session",
    "seed_three_cities",
    "sign_token_with_secret",
    "update_profile",
]

# Silence Path import warning — kept in case future helpers need it.
_ = Path
