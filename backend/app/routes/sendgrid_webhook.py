"""SendGrid Event Webhook ingestion (T12.2a).

Public endpoint:
    POST /api/webhooks/sendgrid/events

Responsibilities:
    1. Verify the ECDSA signature SendGrid attaches to each request using the
       public key configured via ``SENDGRID_WEBHOOK_PUBLIC_KEY`` (PEM).
    2. Persist the raw event to ``sendgrid_events`` for audit.
    3. When a session id is carried on the event's ``unique_args``, also
       append an ``engagement_events`` row keyed by category.
    4. On hard bounce / dropped / spam_report, emit a
       ``reminders_auto_disabled`` engagement event as the signal to stop
       future reminders for that session.

TODO(S12b): When the ``sessions.reminders_enabled BOOLEAN DEFAULT 1`` column
landing ships (likely the T12.19 prerequisite), switch
``_auto_disable_reminders`` to also issue ``UPDATE sessions SET
reminders_enabled=0 WHERE id = ?``. For now, the audit row is the signal and
downstream reminder dispatchers must respect it.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import APIRouter, HTTPException, Request, status

from app.integrations.email.core import (
    log_engagement_event,
    resolve_db_path as _resolve_email_db_path,
)
from app.routes._sendgrid_webhook_db import (
    insert_sendgrid_event,
    log_reminders_auto_disabled,
)

logger = logging.getLogger("app.routes.sendgrid_webhook")

router = APIRouter(prefix="/api/webhooks/sendgrid", tags=["webhooks"])

_SIG_HEADER = "X-Twilio-Email-Event-Webhook-Signature"
_TS_HEADER = "X-Twilio-Email-Event-Webhook-Timestamp"

_HARD_BOUNCE_TYPES = frozenset({"bounce"})
_AUTO_DISABLE_EVENTS = frozenset({"dropped", "spamreport"})
_EVENT_CATEGORY = {
    "delivered": "delivered",
    "open": "open",
    "bounce": "bounce",
    "dropped": "dropped",
    "spamreport": "spam_report",
}

# Lazily-parsed public key, reset to None in tests via monkeypatch.
_cached_public_key: ec.EllipticCurvePublicKey | None = None


# -------------------- Public-key + signature helpers --------------------


def _load_public_key() -> ec.EllipticCurvePublicKey | None:
    """Parse ``SENDGRID_WEBHOOK_PUBLIC_KEY`` (PEM) into a key object."""
    global _cached_public_key
    if _cached_public_key is not None:
        return _cached_public_key
    pem = os.environ.get("SENDGRID_WEBHOOK_PUBLIC_KEY", "").strip()
    if not pem:
        return None
    try:
        key = serialization.load_pem_public_key(pem.encode("ascii"))
    except Exception:
        logger.exception("Failed to parse SENDGRID_WEBHOOK_PUBLIC_KEY")
        return None
    if not isinstance(key, ec.EllipticCurvePublicKey):
        logger.error("SENDGRID_WEBHOOK_PUBLIC_KEY is not an EC public key")
        return None
    _cached_public_key = key
    return key


def _verify_signature(
    signature_b64: str, timestamp: str, body: bytes
) -> bool:
    """Return True iff the ECDSA P-256 signature matches."""
    public_key = _load_public_key()
    if public_key is None:
        return False
    try:
        sig_der = base64.b64decode(signature_b64, validate=False)
    except Exception:
        return False
    signed_blob = timestamp.encode("ascii") + body
    try:
        public_key.verify(sig_der, signed_blob, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return False
    except Exception:
        logger.exception("Unexpected error verifying SendGrid signature")
        return False
    return True


# -------------------- DB path resolution (test-injectable) --------------------


def _resolve_db_path() -> Path | None:
    """Return the sqlite DB path, or None when unresolvable."""
    return _resolve_email_db_path(None)


# -------------------- Event routing --------------------


def _session_id_from(event: dict[str, Any]) -> str | None:
    """Return the session id carried on ``unique_args``, if any."""
    unique_args = event.get("unique_args") or {}
    if not isinstance(unique_args, dict):
        return None
    session_id = unique_args.get("session_id")
    return session_id if isinstance(session_id, str) and session_id else None


def _is_hard_bounce(event: dict[str, Any]) -> bool:
    """Return True iff the event's ``type`` matches SendGrid hard bounce."""
    return str(event.get("type", "")).lower() in _HARD_BOUNCE_TYPES


def _auto_disable_reminders(
    db_path: Path | None, session_id: str, reason: str
) -> None:
    """Emit the audit row that downstream reminder code must respect."""
    log_reminders_auto_disabled(db_path, session_id=session_id, reason=reason)
    logger.info(
        "reminders auto-disabled: session_id=%s reason=%s",
        session_id, reason,
    )


def _process_event(
    event: dict[str, Any], db_path: Path | None
) -> None:
    """Persist one event and fire side effects. Raises for malformed input."""
    event_type = event.get("event")
    if not isinstance(event_type, str) or not event_type:
        raise ValueError("missing event type")
    category = _EVENT_CATEGORY.get(event_type, event_type)
    session_id = _session_id_from(event)
    insert_sendgrid_event(db_path, event_type=event_type, event=event)
    log_engagement_event(
        db_path,
        session_id=session_id,
        category=category,
        payload=event,
    )
    _maybe_auto_disable(event, event_type, session_id, db_path)


def _maybe_auto_disable(
    event: dict[str, Any],
    event_type: str,
    session_id: str | None,
    db_path: Path | None,
) -> None:
    """Dispatch to auto-disable when the event warrants it."""
    if session_id is None:
        return
    if event_type == "bounce" and _is_hard_bounce(event):
        _auto_disable_reminders(db_path, session_id, "hard_bounce")
    elif event_type == "dropped":
        _auto_disable_reminders(db_path, session_id, "dropped")
    elif event_type == "spamreport":
        _auto_disable_reminders(db_path, session_id, "spam_complaint")


# -------------------- Route handler --------------------


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT)
async def receive_sendgrid_events(request: Request) -> None:
    """Verify signature, then process each event in the payload."""
    body = await request.body()
    signature = request.headers.get(_SIG_HEADER)
    timestamp = request.headers.get(_TS_HEADER)
    if not signature or not timestamp:
        logger.warning("SendGrid webhook rejected: missing signature header")
        raise HTTPException(status_code=401, detail="missing signature")
    if not _verify_signature(signature, timestamp, body):
        logger.warning(
            "SendGrid webhook rejected: invalid signature (ts=%s)", timestamp
        )
        raise HTTPException(status_code=401, detail="invalid signature")
    try:
        events = json.loads(body or b"[]")
    except json.JSONDecodeError:
        logger.warning("SendGrid webhook rejected: body is not valid JSON")
        raise HTTPException(status_code=400, detail="invalid JSON") from None
    if not isinstance(events, list):
        events = [events]
    db_path = _resolve_db_path()
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            logger.warning(
                "SendGrid webhook skipped event[%d]: not an object", idx
            )
            continue
        try:
            _process_event(event, db_path)
        except Exception:  # noqa: BLE001 — isolate per-event failures
            logger.warning(
                "SendGrid webhook skipped malformed event[%d]", idx,
                exc_info=True,
            )
