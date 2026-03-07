"""Resource health check — decay detection from feedback patterns."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries_feedback import (
    get_all_feedback_stats,
    update_resource_health,
)
from app.modules.feedback.types import ResourceHealth

MIN_VOTES_FOR_FLAGGED = 3
FLAGGED_THRESHOLD = 0.60
WATCH_THRESHOLD = 0.40


def check_resource_health(total: int, unhelpful_count: int) -> ResourceHealth:
    """Determine health status from feedback stats."""
    if total == 0:
        return ResourceHealth.HEALTHY

    rate = unhelpful_count / total

    if rate >= FLAGGED_THRESHOLD and total >= MIN_VOTES_FOR_FLAGGED:
        return ResourceHealth.FLAGGED
    if rate >= WATCH_THRESHOLD:
        return ResourceHealth.WATCH
    return ResourceHealth.HEALTHY


async def update_all_health_statuses(db: AsyncSession) -> int:
    """Batch update health status for all resources with recent feedback."""
    all_stats = await get_all_feedback_stats(db)
    for stats in all_stats:
        status = check_resource_health(stats["total"], stats["unhelpful_count"])
        await update_resource_health(db, stats["resource_id"], status)
    await db.commit()
    return len(all_stats)
