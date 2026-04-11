"""TWC job adapter — stub until live integration lands in S2."""

from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)
_stub_logged = False


def _log_stub_once() -> None:
    global _stub_logged
    if not _stub_logged:
        _logger.warning("stub: live TWC integration lands in S2")
        _stub_logged = True


_log_stub_once()


class TWCJobAdapter:
    async def fetch_jobs(
        self, session, query: str, location: str
    ) -> list[dict]:
        return []
