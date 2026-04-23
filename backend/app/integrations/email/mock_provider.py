"""Test-only mock SendGrid clients.

Three flavours:

* :class:`MockSendGridClient` — canned success (202 + synthetic message id)
* :class:`FailingMockSendGridClient` — raises on every send
* :class:`FlakeyMockSendGridClient` — raises for the first N calls, then ok

All calls are recorded on ``self.calls`` so tests can inspect payloads.
None of these classes perform any network IO — they are pure Python.
"""

from __future__ import annotations

import uuid
from typing import Any


class _BaseMock:
    """Common call-recorder for mock clients."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []


class MockSendGridClient(_BaseMock):
    """Always-succeeds canned mock SendGrid client."""

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(payload)
        return {
            "status_code": 202,
            "message_id": f"mock-{uuid.uuid4().hex[:12]}",
        }


class FailingMockSendGridClient(_BaseMock):
    """Always raises :class:`RuntimeError` — used for final-failure tests."""

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(payload)
        raise RuntimeError("sendgrid mock: forced failure")


class FlakeyMockSendGridClient(_BaseMock):
    """Fails the first ``fail_first_n`` sends, then succeeds on attempt N+1."""

    def __init__(self, fail_first_n: int = 2) -> None:
        super().__init__()
        self._fail_first_n = fail_first_n

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(payload)
        if len(self.calls) <= self._fail_first_n:
            raise RuntimeError(
                f"sendgrid mock: transient failure {len(self.calls)}"
            )
        return {
            "status_code": 202,
            "message_id": f"mock-{uuid.uuid4().hex[:12]}",
        }
