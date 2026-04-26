"""Regression tests for share-endpoint PII redaction (S13 T13.71/T13.72).

Findings addressed:
- T13.71 P1: ``GET /api/plan/shared/{share_token}`` returned the worker's
  persistent ``session_id`` (UUID) and the full raw ``barriers`` slug list
  (e.g., ``criminal_record``, ``health``, ``housing``) to anyone holding the
  public share URL. Realistic leak via email forwarders / shared inboxes.
- T13.72 medium: The same handler hardcoded ``career_center_phone: ""`` and
  used the *city* name (``"Montgomery"``) as if it were a career center name.

Design decision on ``barriers`` redaction:
  We expose a non-PII ``barriers_count`` integer instead of the raw category
  slugs. Rationale: the share endpoint is intentionally public-with-token, so
  any field that reveals *which* protected categories a worker falls into
  (criminal_record, health, housing, credit, childcare) is a civil-rights /
  HIPAA-shaped leak the moment the URL is forwarded. A scalar count preserves
  the share-narrative value ("this person is working on three things") without
  identifying the categories. The raw ``barriers`` array is dropped entirely.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.routes.share import _rate_limiter


@pytest.fixture(autouse=True)
def _clear_share_rate_limiter():
    """Clear the share-route rate limiter between tests."""
    _rate_limiter.clear()
    yield
    _rate_limiter.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_session(
    *,
    session_id: str,
    auth_token: str,
    barriers: list[str],
    profile: dict | None = None,
) -> None:
    """Insert a session row + feedback token. Optionally a profile JSON blob."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "test",
            "session_id": session_id,
            "barriers": [],
            "immediate_next_steps": ["Visit the career center", "Call about WIOA"],
        })
        await db.execute(
            text(
                "INSERT INTO sessions "
                "(id, created_at, barriers, plan, profile, expires_at) "
                "VALUES (:id, :ts, :b, :p, :pr, :exp)"
            ),
            {
                "id": session_id,
                "ts": now.isoformat(),
                "b": json.dumps(barriers),
                "p": plan,
                "pr": json.dumps(profile) if profile is not None else None,
                "exp": expires,
            },
        )
        await db.execute(
            text(
                "INSERT INTO feedback_tokens "
                "(token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {
                "tok": auth_token,
                "sid": session_id,
                "ts": now.isoformat(),
                "exp": expires,
            },
        )
        await db.commit()


async def _create_share(client, session_id: str, auth_token: str) -> str:
    """POST a share for the session and return the share_token."""
    resp = await client.post(f"/api/plan/{session_id}/share?token={auth_token}")
    assert resp.status_code == 200, resp.text
    return resp.json()["share_token"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSharedResponsePIIRedaction:
    """T13.71 P1 — strip session_id and raw barrier slugs from the public payload."""

    @pytest.mark.anyio
    async def test_shared_response_does_not_include_raw_session_id(
        self, client, test_engine,
    ):
        """The persistent session UUID must NOT appear in the public response.

        Acceptable shapes: no ``session_id`` field at all, or a hash that does
        not match the raw UUID. The raw UUID itself anywhere in the response
        body is a P1 leak.
        """
        sid = "00000000-0000-4000-8000-redaction001"
        await _seed_session(
            session_id=sid,
            auth_token="auth-redact-1",
            barriers=["criminal_record"],
        )
        share_tok = await _create_share(client, sid, "auth-redact-1")

        resp = await client.get(f"/api/plan/shared/{share_tok}")
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" not in data, (
            "session_id leaked in shared response: this is the worker's "
            "persistent backend identifier"
        )
        # Also assert the raw UUID does not appear ANYWHERE in the body
        body_blob = json.dumps(data)
        assert sid not in body_blob, (
            f"raw session_id {sid!r} appears in response body"
        )

    @pytest.mark.anyio
    async def test_shared_response_does_not_include_barrier_detail(
        self, client, test_engine,
    ):
        """Raw barrier slugs are PII (HIPAA/civil-rights shaped) and must be redacted.

        Design decision: we omit the ``barriers`` array entirely and expose
        ``barriers_count`` (a non-identifying integer) so the recipient still
        sees that the worker has identified obstacles, without learning *which*
        protected category they fall into.
        """
        sid = "00000000-0000-4000-8000-redaction002"
        sensitive_barriers = ["criminal_record", "health", "housing"]
        await _seed_session(
            session_id=sid,
            auth_token="auth-redact-2",
            barriers=sensitive_barriers,
        )
        share_tok = await _create_share(client, sid, "auth-redact-2")

        resp = await client.get(f"/api/plan/shared/{share_tok}")
        assert resp.status_code == 200
        data = resp.json()

        # No raw slug should appear anywhere in the response body
        body_blob = json.dumps(data)
        for slug in sensitive_barriers:
            assert slug not in body_blob, (
                f"sensitive barrier slug {slug!r} leaked in shared response"
            )

        # If a `barriers` field exists, it must not be the raw slug list
        assert data.get("barriers") in (None, [], {}) or not isinstance(
            data.get("barriers"), list
        ) or all(
            isinstance(b, str) and b not in sensitive_barriers
            for b in data["barriers"]
        ), "barriers field still contains raw category slugs"

        # We expose a non-PII count so the share remains narratively useful
        assert "barriers_count" in data, (
            "expected barriers_count scalar to preserve share value without PII"
        )
        assert data["barriers_count"] == 3


class TestSharedResponseCareerCenter:
    """T13.72 — career_center_name and career_center_phone must be real values."""

    @pytest.mark.anyio
    async def test_shared_response_career_center_resolved_from_resource_router(
        self, client, test_engine,
    ):
        """Shared response must expose the real career center name + phone.

        The fix sources these from ``get_career_center()`` (the same helper
        ``/api/plan/{sid}/career-center`` uses), NOT a hardcoded empty string
        and the city name. For Montgomery (the default test city) this means
        ``"Montgomery Career Center"`` and the actual phone ``334-286-1746``.
        """
        sid = "00000000-0000-4000-8000-redaction003"
        await _seed_session(
            session_id=sid,
            auth_token="auth-redact-3",
            barriers=["transportation"],
        )
        share_tok = await _create_share(client, sid, "auth-redact-3")

        resp = await client.get(f"/api/plan/shared/{share_tok}")
        assert resp.status_code == 200
        data = resp.json()

        # Name must include "Career Center" — it's a center, not a city
        assert "career_center_name" in data
        assert "Career Center" in data["career_center_name"], (
            f"career_center_name {data['career_center_name']!r} is not a real "
            "center name (looks like the city)"
        )

        # Phone must be a non-empty string with at least 7 digits
        assert "career_center_phone" in data
        phone = data["career_center_phone"]
        digit_count = sum(1 for ch in phone if ch.isdigit())
        assert digit_count >= 7, (
            f"career_center_phone {phone!r} has too few digits to be a real number"
        )

    @pytest.mark.anyio
    async def test_shared_response_handles_missing_career_center_gracefully(
        self, client, test_engine,
    ):
        """If a city has no resolvable career center, the response must still be
        valid JSON with sensibly-empty fields — NOT a hardcoded city name
        masquerading as a center.
        """
        sid = "00000000-0000-4000-8000-redaction004"
        await _seed_session(
            session_id=sid,
            auth_token="auth-redact-4",
            barriers=[],
        )
        share_tok = await _create_share(client, sid, "auth-redact-4")

        resp = await client.get(f"/api/plan/shared/{share_tok}")
        assert resp.status_code == 200
        data = resp.json()
        # Both fields must be present (frontend depends on them)
        assert "career_center_name" in data
        assert "career_center_phone" in data
        # And the name is not just the bare city ("Montgomery") — it must be a
        # real center name OR an explicit empty string. "Montgomery" alone (the
        # city) is the symptom we're fixing.
        name = data["career_center_name"]
        assert name == "" or "Career Center" in name or "Workforce" in name, (
            f"career_center_name {name!r} looks like a bare city name"
        )


class TestSharedResponseStillUseful:
    """Sanity gate — the share feature must not be broken by the PII fix."""

    @pytest.mark.anyio
    async def test_share_link_still_returns_useful_public_safe_content(
        self, client, test_engine,
    ):
        """After the redaction fix, the response still contains the public-safe
        fields a recipient needs to make sense of the share: created_at,
        next_steps, and career_center contact info.
        """
        sid = "00000000-0000-4000-8000-redaction005"
        await _seed_session(
            session_id=sid,
            auth_token="auth-redact-5",
            barriers=["transportation", "training"],
        )
        share_tok = await _create_share(client, sid, "auth-redact-5")

        resp = await client.get(f"/api/plan/shared/{share_tok}")
        assert resp.status_code == 200
        data = resp.json()
        # The share is still useful — these public-safe fields remain
        assert "created_at" in data
        assert "next_steps" in data
        assert isinstance(data["next_steps"], list)
        assert len(data["next_steps"]) >= 1
        assert "career_center_name" in data
        assert "career_center_phone" in data
        # And the count tells the recipient something is being worked on
        assert data.get("barriers_count") == 2
