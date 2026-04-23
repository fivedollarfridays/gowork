"""Tests for SendGrid Event Webhook ingestion (T12.2a).

Covers:
- Router registration in all_routers
- Signature verification (missing / invalid / valid) via ECDSA P-256
- Event handling: delivered, open, bounce (hard/soft), dropped, spam_report
- Batch payloads with per-event error isolation
- Auto-disable audit row on hard bounce / spam / dropped
  (sessions.reminders_enabled column does not exist in current schema —
   audit row is the signal; see route module TODO)
"""

from __future__ import annotations

import base64
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import all_routers
from app.routes import sendgrid_webhook


# -------------------- DB fixture --------------------


@pytest.fixture
def webhook_db(tmp_path: Path) -> Path:
    """Create a temp sqlite DB with the minimum schema the webhook needs."""
    path = tmp_path / "test_webhook.db"
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


# -------------------- Keypair + signature fixtures --------------------


@pytest.fixture
def keypair():
    """Generate an ECDSA P-256 test keypair for signing payloads."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_key, pub_pem.decode("ascii")


def _sign(private_key, timestamp: str, body: bytes) -> str:
    """Sign `timestamp + body` with ECDSA-SHA256 and return base64 DER."""
    signed_blob = timestamp.encode("ascii") + body
    sig_der = private_key.sign(signed_blob, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig_der).decode("ascii")


@pytest.fixture
def app_client(keypair, webhook_db, monkeypatch):
    """Build a minimal FastAPI app with only the sendgrid webhook router."""
    _, pub_pem = keypair
    monkeypatch.setenv("SENDGRID_WEBHOOK_PUBLIC_KEY", pub_pem)
    monkeypatch.setattr(sendgrid_webhook, "_cached_public_key", None)
    monkeypatch.setattr(
        sendgrid_webhook, "_resolve_db_path", lambda: webhook_db
    )
    app = FastAPI()
    app.include_router(sendgrid_webhook.router)
    return TestClient(app)


# -------------------- Query helpers --------------------


def _engagement_rows(db_path: Path) -> list[tuple[str, str, dict]]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT session_id, category, payload_json FROM engagement_events "
            "ORDER BY id ASC"
        ).fetchall()
    finally:
        conn.close()
    return [(r[0], r[1], json.loads(r[2]) if r[2] else {}) for r in rows]


def _sendgrid_rows(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT event_type, email, message_id, reason FROM sendgrid_events "
            "ORDER BY id ASC"
        ).fetchall()
    finally:
        conn.close()
    return [
        {"event_type": r[0], "email": r[1], "message_id": r[2], "reason": r[3]}
        for r in rows
    ]


def _post_signed(client, private_key, events: list[dict]) -> object:
    import time as _time
    body = json.dumps(events).encode("utf-8")
    # Use current timestamp — webhook now rejects stale (>10min) timestamps.
    timestamp = str(int(_time.time()))
    signature = _sign(private_key, timestamp, body)
    return client.post(
        "/api/webhooks/sendgrid/events",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Twilio-Email-Event-Webhook-Signature": signature,
            "X-Twilio-Email-Event-Webhook-Timestamp": timestamp,
        },
    )


# -------------------- Router registration --------------------


def test_router_registered_in_all_routers():
    assert sendgrid_webhook.router in all_routers


# -------------------- Signature verification --------------------


def test_missing_signature_returns_401(app_client):
    body = json.dumps([{"event": "delivered", "email": "a@b.com"}]).encode()
    response = app_client.post(
        "/api/webhooks/sendgrid/events",
        content=body,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_invalid_signature_returns_401(app_client, caplog):
    body = json.dumps([{"event": "delivered", "email": "a@b.com"}]).encode()
    response = app_client.post(
        "/api/webhooks/sendgrid/events",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Twilio-Email-Event-Webhook-Signature": "not-a-real-signature",
            "X-Twilio-Email-Event-Webhook-Timestamp": "1700000000",
        },
    )
    assert response.status_code == 401
    assert any(
        "signature" in rec.message.lower() and rec.levelname == "WARNING"
        for rec in caplog.records
    )


def test_valid_signature_accepts_payload(app_client, keypair):
    private_key, _ = keypair
    events = [
        {
            "event": "delivered",
            "email": "user@example.com",
            "sg_message_id": "mid-1",
            "timestamp": 1700000000,
            "unique_args": {"session_id": "sess-1"},
        }
    ]
    response = _post_signed(app_client, private_key, events)
    assert response.status_code == 204


# -------------------- Event ingestion: delivered / open --------------------


def test_delivered_event_writes_both_tables(app_client, keypair, webhook_db):
    private_key, _ = keypair
    events = [
        {
            "event": "delivered",
            "email": "user@example.com",
            "sg_message_id": "mid-d1",
            "timestamp": 1700000000,
            "unique_args": {"session_id": "sess-1"},
        }
    ]
    response = _post_signed(app_client, private_key, events)
    assert response.status_code == 204

    eng = _engagement_rows(webhook_db)
    sg = _sendgrid_rows(webhook_db)
    assert [r[1] for r in eng] == ["delivered"]
    assert eng[0][0] == "sess-1"
    assert [r["event_type"] for r in sg] == ["delivered"]
    assert sg[0]["email"] == "user@example.com"
    assert sg[0]["message_id"] == "mid-d1"


def test_open_event_writes_both_tables(app_client, keypair, webhook_db):
    private_key, _ = keypair
    events = [
        {
            "event": "open",
            "email": "user@example.com",
            "sg_message_id": "mid-o1",
            "timestamp": 1700000000,
            "unique_args": {"session_id": "sess-1"},
        }
    ]
    response = _post_signed(app_client, private_key, events)
    assert response.status_code == 204
    assert [r[1] for r in _engagement_rows(webhook_db)] == ["open"]
    assert [r["event_type"] for r in _sendgrid_rows(webhook_db)] == ["open"]


# -------------------- Auto-disable flows --------------------


def test_hard_bounce_auto_disables(app_client, keypair, webhook_db):
    private_key, _ = keypair
    events = [
        {
            "event": "bounce",
            "type": "bounce",  # SendGrid marks hard bounces with type=bounce
            "email": "user@example.com",
            "sg_message_id": "mid-b1",
            "reason": "550 mailbox does not exist",
            "timestamp": 1700000000,
            "unique_args": {"session_id": "sess-1"},
        }
    ]
    response = _post_signed(app_client, private_key, events)
    assert response.status_code == 204

    categories = [r[1] for r in _engagement_rows(webhook_db)]
    assert "bounce" in categories
    assert "reminders_auto_disabled" in categories
    auto_row = next(
        r for r in _engagement_rows(webhook_db)
        if r[1] == "reminders_auto_disabled"
    )
    assert auto_row[2]["reason"] == "hard_bounce"
    assert auto_row[2]["session_id"] == "sess-1"


def test_soft_bounce_logs_only(app_client, keypair, webhook_db):
    private_key, _ = keypair
    events = [
        {
            "event": "bounce",
            "type": "blocked",  # soft
            "email": "user@example.com",
            "sg_message_id": "mid-b2",
            "timestamp": 1700000000,
            "unique_args": {"session_id": "sess-1"},
        }
    ]
    response = _post_signed(app_client, private_key, events)
    assert response.status_code == 204

    categories = [r[1] for r in _engagement_rows(webhook_db)]
    assert "bounce" in categories
    assert "reminders_auto_disabled" not in categories


def test_spam_report_auto_disables(app_client, keypair, webhook_db):
    private_key, _ = keypair
    events = [
        {
            "event": "spamreport",
            "email": "user@example.com",
            "sg_message_id": "mid-s1",
            "timestamp": 1700000000,
            "unique_args": {"session_id": "sess-1"},
        }
    ]
    response = _post_signed(app_client, private_key, events)
    assert response.status_code == 204

    rows = _engagement_rows(webhook_db)
    categories = [r[1] for r in rows]
    assert "spam_report" in categories
    assert "reminders_auto_disabled" in categories
    auto_row = next(r for r in rows if r[1] == "reminders_auto_disabled")
    assert auto_row[2]["reason"] == "spam_complaint"


def test_dropped_event_treated_as_hard_bounce(
    app_client, keypair, webhook_db
):
    private_key, _ = keypair
    events = [
        {
            "event": "dropped",
            "email": "user@example.com",
            "sg_message_id": "mid-dr1",
            "reason": "Invalid SMTPAPI header",
            "timestamp": 1700000000,
            "unique_args": {"session_id": "sess-1"},
        }
    ]
    response = _post_signed(app_client, private_key, events)
    assert response.status_code == 204

    categories = [r[1] for r in _engagement_rows(webhook_db)]
    assert "dropped" in categories
    assert "reminders_auto_disabled" in categories


# -------------------- Batch handling --------------------


def test_batch_payload(app_client, keypair, webhook_db):
    private_key, _ = keypair
    events = [
        {
            "event": "delivered", "email": "a@b.com",
            "sg_message_id": "m1", "timestamp": 1700000000,
            "unique_args": {"session_id": "sess-1"},
        },
        {
            "event": "open", "email": "a@b.com",
            "sg_message_id": "m1", "timestamp": 1700000100,
            "unique_args": {"session_id": "sess-1"},
        },
        {
            "event": "delivered", "email": "c@d.com",
            "sg_message_id": "m2", "timestamp": 1700000200,
            "unique_args": {"session_id": "sess-1"},
        },
    ]
    response = _post_signed(app_client, private_key, events)
    assert response.status_code == 204
    sg_rows = _sendgrid_rows(webhook_db)
    assert len(sg_rows) == 3
    assert [r["event_type"] for r in sg_rows] == [
        "delivered", "open", "delivered"
    ]


def test_one_bad_event_doesnt_abort_batch(
    app_client, keypair, webhook_db, caplog
):
    private_key, _ = keypair
    events = [
        {
            "event": "delivered", "email": "a@b.com",
            "sg_message_id": "m1", "timestamp": 1700000000,
            "unique_args": {"session_id": "sess-1"},
        },
        {"not_an_event": True},  # malformed — missing `event`
        {
            "event": "open", "email": "c@d.com",
            "sg_message_id": "m2", "timestamp": 1700000200,
            "unique_args": {"session_id": "sess-1"},
        },
    ]
    response = _post_signed(app_client, private_key, events)
    assert response.status_code == 204
    sg_rows = _sendgrid_rows(webhook_db)
    assert len(sg_rows) == 2  # the good two
    assert [r["event_type"] for r in sg_rows] == ["delivered", "open"]
