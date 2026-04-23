"""Real SendGrid provider adapter (T12.2).

Kept in its own module so :mod:`sendgrid_client` stays focused on the
retry / audit / flag logic. This file is the only place the live SendGrid
SDK is imported; tests monkeypatch :func:`_build_client` on
:mod:`sendgrid_client` so the SDK is never loaded during unit tests.
"""

from __future__ import annotations

import os
from typing import Any


class RealSendGridClient:
    """Thin adapter around the SendGrid SDK exposing a ``send`` method."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send via the SendGrid SDK. Raises on non-2xx responses."""
        if not self._api_key:
            raise RuntimeError("SENDGRID_API_KEY is not set")
        # Lazy import so tests never need the SDK installed.
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=os.environ.get(
                "SENDGRID_FROM_EMAIL", "noreply@montgowork.local"
            ),
            to_emails=payload["to"],
            subject=payload["subject"],
            plain_text_content=payload["text"],
            html_content=payload["html"],
        )
        for cat in payload.get("categories", []):
            message.add_category(cat)
        client = SendGridAPIClient(self._api_key)
        resp = client.send(message)
        if resp.status_code >= 300:
            raise RuntimeError(
                f"sendgrid returned status {resp.status_code}"
            )
        message_id = getattr(resp, "headers", {}).get("X-Message-Id", "")
        return {"status_code": resp.status_code, "message_id": message_id}
