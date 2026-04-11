"""TWC job adapter — stub until live integration lands in S2."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_logger = logging.getLogger(__name__)
_stub_logged = False


def _log_stub_once() -> None:
    global _stub_logged
    if not _stub_logged:
        _logger.warning("stub: live TWC integration lands in S2")
        _stub_logged = True


class TWCJobAdapter:
    async def fetch_jobs(
        self, session: AsyncSession, query: str, location: str
    ) -> list[dict]:
        _log_stub_once()
        return []
