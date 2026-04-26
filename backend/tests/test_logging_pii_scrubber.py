"""Tests for the centralized PII scrubber structlog processor (T13.94).

The scrubber lives in ``app.core.logging`` and runs in the structlog
processor chain BEFORE the renderer. Its job is to hash known-PII keys
at event-emit time so future call sites get coverage automatically —
no per-site ``hash_session_id`` discipline required.

Tested behaviors:
    - hashes ``session_id`` and replaces with ``session_id_hash``
    - hashes the email family (``email``, ``to_email``, ``from_email``)
    - hashes ``phone`` and ``actor_email``
    - non-PII fields (``request_id``, ``error_class``) pass through
    - missing keys → no error, no extra fields
    - ``None`` value → no error, no fake hash emitted
    - idempotent: pre-hashed (``session_id_hash``) is not re-hashed
"""

from __future__ import annotations

import pytest

from app.core.logging import _PII_KEYS, _scrub_pii
from app.modules.compliance._audit import hash_session_id


@pytest.fixture
def scrub():
    """Bind the processor with placeholder logger/method_name args."""

    def _call(event_dict: dict) -> dict:
        return _scrub_pii(None, "info", event_dict)

    return _call


def test_pii_keys_includes_expected_fields():
    """Sanity check the configured key list — drives all other tests."""
    expected = {
        "session_id",
        "email",
        "to_email",
        "from_email",
        "phone",
        "actor_email",
    }
    assert expected.issubset(set(_PII_KEYS))


def test_scrubber_hashes_session_id(scrub):
    raw = "abc-123-session"
    out = scrub({"event": "warn", "session_id": raw})
    assert "session_id" not in out
    assert out["session_id_hash"] == hash_session_id(raw)


def test_scrubber_hashes_email(scrub):
    out = scrub({"event": "warn", "email": "user@example.com"})
    assert "email" not in out
    assert out["email_hash"] == hash_session_id("user@example.com")


def test_scrubber_hashes_to_email(scrub):
    out = scrub({"event": "warn", "to_email": "to@example.com"})
    assert "to_email" not in out
    assert out["to_email_hash"] == hash_session_id("to@example.com")


def test_scrubber_hashes_from_email(scrub):
    out = scrub({"event": "warn", "from_email": "from@example.com"})
    assert "from_email" not in out
    assert out["from_email_hash"] == hash_session_id("from@example.com")


def test_scrubber_hashes_actor_email(scrub):
    out = scrub({"event": "warn", "actor_email": "advisor@example.com"})
    assert "actor_email" not in out
    assert out["actor_email_hash"] == hash_session_id("advisor@example.com")


def test_scrubber_hashes_phone(scrub):
    out = scrub({"event": "warn", "phone": "+15551234567"})
    assert "phone" not in out
    assert out["phone_hash"] == hash_session_id("+15551234567")


def test_scrubber_preserves_non_pii_fields(scrub):
    out = scrub(
        {
            "event": "ok",
            "request_id": "req-99",
            "error_class": "ValueError",
            "count": 7,
        }
    )
    assert out["event"] == "ok"
    assert out["request_id"] == "req-99"
    assert out["error_class"] == "ValueError"
    assert out["count"] == 7


def test_scrubber_handles_missing_keys(scrub):
    out = scrub({"event": "ok", "request_id": "req-1"})
    # No PII keys present, so no *_hash keys should appear.
    assert all(not k.endswith("_hash") for k in out.keys())
    assert out == {"event": "ok", "request_id": "req-1"}


def test_scrubber_handles_none_value(scrub):
    out = scrub({"event": "warn", "session_id": None})
    # Falsy value → drop, do NOT emit a hash of "None".
    assert "session_id" not in out
    assert "session_id_hash" not in out


def test_scrubber_handles_empty_string(scrub):
    out = scrub({"event": "warn", "email": ""})
    assert "email" not in out
    assert "email_hash" not in out


def test_scrubber_idempotent_on_prehashed(scrub):
    """If the caller already passed ``session_id_hash``, do not re-hash."""
    pre = hash_session_id("already-hashed")
    out = scrub({"event": "warn", "session_id_hash": pre})
    # Hash should pass through unchanged.
    assert out["session_id_hash"] == pre
    # And we should NOT double-encode by treating the hash as raw PII.
    assert "session_id_hash_hash" not in out


def test_scrubber_mixed_pii_and_safe(scrub):
    out = scrub(
        {
            "event": "career_center_warn",
            "session_id": "sess-1",
            "request_id": "req-2",
            "phone": "+1-555",
        }
    )
    assert "session_id" not in out
    assert "phone" not in out
    assert out["session_id_hash"] == hash_session_id("sess-1")
    assert out["phone_hash"] == hash_session_id("+1-555")
    assert out["request_id"] == "req-2"
    assert out["event"] == "career_center_warn"


def test_scrubber_returns_event_dict(scrub):
    """Processor contract: must return event_dict (not None)."""
    out = scrub({"event": "x"})
    assert isinstance(out, dict)


def test_scrubber_in_processor_chain():
    """Integration smoke: bind a logger configured with _scrub_pii and
    confirm the captured event has the raw key removed and the hash present.
    """
    import structlog

    structlog.reset_defaults()
    captured: list[dict] = []

    def _capture(_logger, _method_name, event_dict):
        captured.append(dict(event_dict))
        return event_dict

    try:
        structlog.configure(
            processors=[_scrub_pii, _capture, structlog.processors.KeyValueRenderer()],
            wrapper_class=structlog.BoundLogger,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=False,
        )
        log = structlog.get_logger("t13_94_test")
        log.warning("invalid_credit_profile", session_id="raw-session-xyz")
    finally:
        structlog.reset_defaults()

    assert captured, "processor chain did not capture the event"
    event = captured[0]
    assert "session_id" not in event
    assert event["session_id_hash"] == hash_session_id("raw-session-xyz")
