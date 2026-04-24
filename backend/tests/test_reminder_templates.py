"""Tests for engagement.reminder_templates — unsubscribe URL signer.

Critical behaviors:
- ``build_unsubscribe_url`` embeds a real signed token (not a stub) so
  the URL round-trips through ``unsubscribe_tokens.verify``.
- The signer raises when ``UNSUBSCRIBE_TOKEN_SECRET`` is unset (fail
  closed — the previous stub silently produced un-verifiable links).
- ``render_reminder`` and ``render_digest_wrapper`` interpolate the
  signed URL into both HTML and text bodies.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from app.core.migrations import runner
from app.modules.common.temporal_types import StallLevel

_SECRET = "rt-unsub-secret-for-tests-0123456789abcdef"


@pytest.fixture
def migrated_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "rt-unsub.db")
    runner.apply_pending(db_path)
    return db_path


@pytest.fixture
def secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNSUBSCRIBE_TOKEN_SECRET", _SECRET)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)


def _extract_token(url: str) -> str:
    qs = parse_qs(urlparse(url).query)
    assert "token" in qs, f"unsubscribe URL missing ?token=: {url}"
    return qs["token"][0]


def test_build_unsubscribe_url_embeds_verifiable_token(
    migrated_db: str, secret_env: None,
) -> None:
    """The token in the URL must verify back to the same session id."""
    from app.modules.engagement import reminder_templates, unsubscribe_tokens

    url = reminder_templates.build_unsubscribe_url("sess-123")
    token = _extract_token(url)
    assert not token.startswith("stub-"), (
        f"unsubscribe URL still using stub token: {token!r}"
    )
    assert unsubscribe_tokens.verify(token, db_path=migrated_db) == "sess-123"


def test_build_unsubscribe_url_requires_secret_env(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing UNSUBSCRIBE_TOKEN_SECRET must fail closed (not return a stub)."""
    from app.modules.engagement import reminder_templates

    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET", raising=False)
    monkeypatch.delenv("UNSUBSCRIBE_TOKEN_SECRET_OLD", raising=False)
    with pytest.raises(RuntimeError):
        reminder_templates.build_unsubscribe_url("sess-x")


def test_render_reminder_embeds_signed_url(
    migrated_db: str, secret_env: None,
) -> None:
    """SOFT reminder body contains the unsubscribe URL with a real token."""
    from app.modules.engagement import reminder_templates, unsubscribe_tokens

    rendered = reminder_templates.render_reminder(
        StallLevel.SOFT,
        first_name="Jordan",
        session_id="sess-soft",
        days_stalled=3,
    )
    # Both bodies carry the unsub link.
    assert "/api/engagement/unsubscribe?token=" in rendered.html
    assert "/api/engagement/unsubscribe?token=" in rendered.text
    # The text body has the raw URL — extract + verify it.
    text_url = next(
        line.split("Unsubscribe: ", 1)[1].strip()
        for line in rendered.text.splitlines()
        if "Unsubscribe: " in line
    )
    token = _extract_token(text_url)
    assert (
        unsubscribe_tokens.verify(token, db_path=migrated_db) == "sess-soft"
    )


def test_render_digest_wrapper_embeds_signed_url(
    migrated_db: str, secret_env: None,
) -> None:
    """Digest wrapper appends a CAN-SPAM unsubscribe footer with real token."""
    from app.modules.engagement import reminder_templates, unsubscribe_tokens

    rendered = reminder_templates.render_digest_wrapper(
        subject="Weekly digest",
        html_body="<p>Hello</p>",
        text_body="Hello",
        session_id="sess-digest",
    )
    assert "/api/engagement/unsubscribe?token=" in rendered.html
    text_url = next(
        line.split("Unsubscribe: ", 1)[1].strip()
        for line in rendered.text.splitlines()
        if "Unsubscribe: " in line
    )
    token = _extract_token(text_url)
    assert (
        unsubscribe_tokens.verify(token, db_path=migrated_db)
        == "sess-digest"
    )
