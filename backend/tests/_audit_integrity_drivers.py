"""Request drivers + DB helpers for the audit-integrity test (T13.59).

Extracted from :mod:`tests.test_audit_integrity` so the test file
stays under the 600-line architecture limit. Each helper is pure (no
pytest fixtures) and one driver per :class:`AuditShape` entry — the
test loop iterates over ``DRIVERS`` and verifies a +1 row delta.

Per-iteration context
---------------------
Drivers take a :class:`DriverContext` so the test loop can vary the
session id between iterations. Distinct session ids are essential for
the unsubscribe drivers — :func:`unsubscribe_tokens.sign` is fully
deterministic for a given (session_id, secret, instant) tuple, so two
calls within the same second produce the same token, which the
single-use guard rejects on replay. Varying ``session_id`` across
iterations sidesteps that without disabling the dedup guard.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests._audit_integrity_fixtures import AuditShape


# --------------------------------------------------------------- constants

DEFAULT_SESSION_ID = "11111111-2222-3333-4444-555555555555"
DEFAULT_FEEDBACK_TOKEN = "tok-audit-integrity-feedback-aaaaaaaa"
ADMIN_KEY = "test-admin-key-for-audit-integrity-suite-x32"
ADVISOR_TOKEN = "mw_adv_audit_integrity_test_token_x32x"
ADVISOR_ID = "adv-audit-integrity"
CITY = "montgomery"
UNSUB_SECRET = "unsub-audit-integrity-secret-0123456789abcd"
COMPLIANCE_SECRET = "compliance-audit-integrity-secret-0123456789abcd"
WORKER_EMAIL = "worker.under.test@example.com"
WORKER_FIRST_NAME = "WorkerFirstName"


# --------------------------------------------------------------- DriverContext


@dataclass(frozen=True)
class DriverContext:
    """Per-iteration request context (lets the test loop vary session id)."""

    session_id: str
    feedback_token: str


def ctx_default() -> DriverContext:
    """Return the canonical default context (used by smoke/pinned tests)."""
    return DriverContext(
        session_id=DEFAULT_SESSION_ID,
        feedback_token=DEFAULT_FEEDBACK_TOKEN,
    )


def iteration_session_id(idx: int) -> str:
    """Deterministic UUID-shaped session id per iteration index."""
    base = "0aaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    leading = format(idx % 16, "x")
    return f"{leading}{base[1:]}"


def iteration_feedback_token(idx: int) -> str:
    """Deterministic feedback-token plaintext per iteration index."""
    return f"tok-audit-iter-{idx:02d}-pad-pad-pad-pad-pad"


def iteration_context(idx: int) -> DriverContext:
    """Bundle the iteration session id + token into a DriverContext."""
    return DriverContext(
        session_id=iteration_session_id(idx),
        feedback_token=iteration_feedback_token(idx),
    )


# --------------------------------------------------------------- DB helpers


def seed_session_and_token(
    db_path: str,
    *,
    session_id: str = DEFAULT_SESSION_ID,
    feedback_token: str = DEFAULT_FEEDBACK_TOKEN,
) -> None:
    """Re-seed a worker session + feedback token + record_profiles row.

    Idempotent: if the session has been deleted by a prior driver
    (full_delete cascade), this re-creates it so the next driver can
    proceed.
    """
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=30)).isoformat()
    profile = json.dumps(
        {"email": WORKER_EMAIL, "first_name": WORKER_FIRST_NAME},
    )
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO sessions "
            "(id, created_at, barriers, profile, expires_at, demo) "
            "VALUES (?, ?, '[]', ?, ?, 0)",
            (session_id, now.isoformat(), profile, expires),
        )
        conn.execute(
            "INSERT OR IGNORE INTO feedback_tokens "
            "(token, session_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (feedback_token, session_id, now.isoformat(), expires),
        )
        conn.execute(
            "INSERT OR IGNORE INTO record_profiles "
            "(session_id, record_types, charge_categories, created_at) "
            "VALUES (?, '[]', '[]', ?)",
            (session_id, now.isoformat()),
        )
        _seed_outcome_if_absent(conn, session_id, now)
        conn.commit()
    finally:
        conn.close()


def _seed_outcome_if_absent(
    conn: sqlite3.Connection, session_id: str, now: datetime,
) -> None:
    """Seed one outcomes_records row if none exists for ``session_id``."""
    existing = conn.execute(
        "SELECT 1 FROM outcomes_records WHERE session_id = ? LIMIT 1",
        (session_id,),
    ).fetchone()
    if existing is None:
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                session_id, "appointment_attended",
                json.dumps({"city": CITY}),
                (now - timedelta(days=14)).isoformat(),
            ),
        )


def seed_advisor_token(db_path: str) -> None:
    """Insert one row into ``advisor_tokens`` so the inbox auth dependency passes."""
    from app.core.advisor_auth import hash_token

    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO advisor_tokens "
            "(token_hash, advisor_id, city, issued_at, revoked_at, expires_at) "
            "VALUES (?, ?, ?, ?, NULL, ?)",
            (
                hash_token(ADVISOR_TOKEN), ADVISOR_ID, CITY,
                now.isoformat(), expires,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def row_count(db_path: str, table: str, where: str = "") -> int:
    """SELECT COUNT(*) from ``table``, optionally with ``where`` clause."""
    sql = f"SELECT COUNT(*) FROM {table}"
    if where:
        sql += f" WHERE {where}"
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(sql).fetchone()
    finally:
        conn.close()
    return int(row[0])


def build_where(shape: AuditShape, *, session_id: str | None = None) -> str:
    """Render the WHERE clause for the audit-shape filter.

    When ``session_id`` is supplied AND the table carries a session
    identifier we can filter on, the clause is narrowed to that
    session — necessary so the per-iteration delta check ignores rows
    from earlier iterations of the same loop.
    """
    parts: list[str] = []
    if shape.category_filter:
        parts.append(f"category = '{shape.category_filter}'")
    if shape.action_filter:
        parts.append(f"action = '{shape.action_filter}'")
    if session_id is not None:
        if shape.table == "compliance_audit":
            from app.modules.compliance._audit import hash_session_id
            parts.append(
                f"session_id_hash = '{hash_session_id(session_id)}'",
            )
        elif shape.table == "engagement_events":
            parts.append(f"session_id = '{session_id}'")
    return " AND ".join(parts)


# --------------------------------------------------------------- drivers


def _sign_unsub_token(session_id: str) -> str:
    from app.modules.engagement import unsubscribe_tokens
    return unsubscribe_tokens.sign(session_id)


def drive_compliance_export(
    client: TestClient, ctx: DriverContext = ctx_default(),
) -> Any:
    return client.post(
        "/api/compliance/export",
        json={
            "session_id": ctx.session_id,
            "session_token": ctx.feedback_token,
        },
    )


def drive_compliance_delete(
    client: TestClient, ctx: DriverContext = ctx_default(),
) -> Any:
    return client.post(
        "/api/compliance/delete",
        json={
            "session_id": ctx.session_id,
            "session_token": ctx.feedback_token,
            "confirm": "DELETE",
            "reason": "audit_integrity_test",
        },
    )


def drive_compliance_selective_delete(
    client: TestClient, ctx: DriverContext = ctx_default(),
) -> Any:
    return client.post(
        "/api/compliance/delete/selective",
        json={
            "session_id": ctx.session_id,
            "session_token": ctx.feedback_token,
            "category": "criminal_record",
            "reason": "audit_integrity_test",
        },
    )


def drive_admin_flag_toggle(
    client: TestClient, ctx: DriverContext = ctx_default(),
) -> Any:
    flag = f"AUDIT_TEST_FLAG_{ctx.session_id[:8]}"
    return client.post(
        f"/api/admin/flags/{flag}",
        headers={"X-Admin-Key": ADMIN_KEY},
        json={"enabled": True, "reason": "audit_integrity_test"},
    )


def drive_advisor_note(
    client: TestClient, ctx: DriverContext = ctx_default(),
    monkeypatch: pytest.MonkeyPatch | None = None,
) -> Any:
    """POST advisor note. Stubs the reminder engine when monkeypatch is given."""
    from app.modules.engagement import reminder_engine

    class _Result:
        success = True
        skipped_reason = None
        category = "advisor_note"
        message_id = "msg-audit-integrity"

    if monkeypatch is not None:
        monkeypatch.setattr(
            reminder_engine, "send_advisor_note",
            lambda *a, **kw: _Result(), raising=False,
        )
    return client.post(
        f"/api/advisor/sessions/{ctx.session_id}/note",
        headers={"X-Admin-Key": ADVISOR_TOKEN},
        json={"message": "Audit-integrity note."},
    )


def drive_engagement_preferences_disable(
    client: TestClient, ctx: DriverContext = ctx_default(),
) -> Any:
    return client.post(
        f"/api/engagement/preferences"
        f"?session_id={ctx.session_id}&token={ctx.feedback_token}",
        json={"reminders_enabled": False},
    )


def drive_engagement_unsubscribe_post(
    client: TestClient, ctx: DriverContext = ctx_default(),
) -> Any:
    return client.post(
        "/api/engagement/unsubscribe",
        json={"token": _sign_unsub_token(ctx.session_id)},
    )


def drive_engagement_unsubscribe_get(
    client: TestClient, ctx: DriverContext = ctx_default(),
) -> Any:
    return client.get(
        f"/api/engagement/unsubscribe"
        f"?token={_sign_unsub_token(ctx.session_id)}",
    )


# Ordered map: "METHOD path" -> driver. Keep the keys identical to
# ``EXPECTED_AUDIT_SHAPES`` so the coverage cross-check stays trivial.
DRIVERS: dict[str, Any] = {
    "POST /api/compliance/export": drive_compliance_export,
    "POST /api/compliance/delete": drive_compliance_delete,
    "POST /api/compliance/delete/selective": drive_compliance_selective_delete,
    "POST /api/admin/flags/{name}": drive_admin_flag_toggle,
    "POST /api/advisor/sessions/{session_id}/note": drive_advisor_note,
    "POST /api/engagement/preferences": drive_engagement_preferences_disable,
    "POST /api/engagement/unsubscribe": drive_engagement_unsubscribe_post,
    "GET /api/engagement/unsubscribe": drive_engagement_unsubscribe_get,
}


__all__ = [
    "ADMIN_KEY", "ADVISOR_ID", "ADVISOR_TOKEN", "CITY",
    "COMPLIANCE_SECRET", "DEFAULT_FEEDBACK_TOKEN", "DEFAULT_SESSION_ID",
    "DRIVERS", "DriverContext", "UNSUB_SECRET",
    "WORKER_EMAIL", "WORKER_FIRST_NAME",
    "build_where", "ctx_default", "drive_advisor_note",
    "drive_compliance_delete", "drive_compliance_export",
    "drive_compliance_selective_delete",
    "drive_engagement_preferences_disable",
    "drive_engagement_unsubscribe_get", "drive_engagement_unsubscribe_post",
    "drive_admin_flag_toggle",
    "iteration_context", "iteration_feedback_token",
    "iteration_session_id", "row_count",
    "seed_advisor_token", "seed_session_and_token",
]
