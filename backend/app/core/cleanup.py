"""Expired session cleanup to prevent PII accumulation."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_GRACE_HOURS = 48
_RELATED_TABLES = ("feedback_tokens", "visit_feedback", "resource_feedback", "record_profiles")

_EXPIRED_SUBQUERY = (
    "SELECT id FROM sessions WHERE expires_at IS NOT NULL AND expires_at < :cutoff"
)


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """Delete sessions expired more than 48 hours ago and their associated data.

    Uses subquery-based DELETEs to avoid loading all IDs into memory.
    Returns the number of sessions deleted.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=_GRACE_HOURS)).isoformat()
    params = {"cutoff": cutoff}

    for table in _RELATED_TABLES:
        # SAFETY: table names come from _RELATED_TABLES (hardcoded constant above).
        await db.execute(
            text(f"DELETE FROM {table} WHERE session_id IN ({_EXPIRED_SUBQUERY})"),
            params,
        )

    result = await db.execute(
        text("DELETE FROM sessions WHERE expires_at IS NOT NULL AND expires_at < :cutoff"),
        params,
    )
    count = result.rowcount
    await db.commit()

    if count:
        logger.info("Cleaned up %d expired sessions", count)
    return count
