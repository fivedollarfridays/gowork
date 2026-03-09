"""Database queries for feedback tables."""

import hmac
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feedback.tokens import generate_token
from app.modules.feedback.types import ResourceFeedbackRequest, ResourceHealth


async def create_feedback_token(db: AsyncSession, session_id: str) -> str:
    """Generate and store a feedback token with 30-day expiry."""
    token = generate_token()
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=30)).isoformat()
    now = now.isoformat()
    await db.execute(
        text(
            "INSERT OR IGNORE INTO feedback_tokens (token, session_id, created_at, expires_at) "
            "VALUES (:token, :session_id, :created_at, :expires_at)"
        ),
        {"token": token, "session_id": session_id, "created_at": now, "expires_at": expires},
    )
    await db.commit()
    return token


async def session_exists(db: AsyncSession, session_id: str) -> bool:
    """Check if a non-expired session exists in the database."""
    now = datetime.now(timezone.utc).isoformat()
    result = await db.execute(
        text("SELECT 1 FROM sessions WHERE id = :sid AND expires_at > :now"),
        {"sid": session_id, "now": now},
    )
    return result.fetchone() is not None


async def insert_resource_feedback(db: AsyncSession, feedback: ResourceFeedbackRequest) -> None:
    """Upsert resource feedback — one vote per resource per session."""
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text(
            "INSERT INTO resource_feedback (resource_id, session_id, helpful, barrier_type, submitted_at) "
            "VALUES (:resource_id, :session_id, :helpful, :barrier_type, :submitted_at) "
            "ON CONFLICT (resource_id, session_id) DO UPDATE SET "
            "helpful = :helpful, barrier_type = :barrier_type, submitted_at = :submitted_at"
        ),
        {
            "resource_id": feedback.resource_id,
            "session_id": feedback.session_id,
            "helpful": int(feedback.helpful),
            "barrier_type": feedback.barrier_type,
            "submitted_at": now,
        },
    )
    await db.commit()


async def validate_token(db: AsyncSession, token: str) -> str | None:
    """Validate a feedback token. Returns session_id if valid and unexpired, else None.

    HIGH-4: Uses hmac.compare_digest as a secondary constant-time check after
    the SQL lookup. The 96-bit token entropy makes timing attacks impractical,
    but the constant-time comparison adds defense-in-depth.
    """
    now = datetime.now(timezone.utc).isoformat()
    result = await db.execute(
        text(
            "SELECT token, session_id FROM feedback_tokens "
            "WHERE token = :token AND expires_at > :now"
        ),
        {"token": token, "now": now},
    )
    row = result.fetchone()
    if row is None:
        return None
    stored_token, session_id = row[0], row[1]
    if not hmac.compare_digest(token, stored_token):
        return None
    return session_id


async def token_exists(db: AsyncSession, token: str) -> bool:
    """Check if a token exists in the database (regardless of expiry)."""
    result = await db.execute(
        text("SELECT 1 FROM feedback_tokens WHERE token = :token"),
        {"token": token},
    )
    return result.fetchone() is not None


async def has_visit_feedback(db: AsyncSession, session_id: str) -> bool:
    """Check if visit feedback already exists for this session."""
    result = await db.execute(
        text("SELECT 1 FROM visit_feedback WHERE session_id = :sid"),
        {"sid": session_id},
    )
    return result.fetchone() is not None


async def insert_visit_feedback(
    db: AsyncSession,
    session_id: str,
    made_it_to_center: int,
    outcomes_json: str,
    plan_accuracy: int,
    free_text: str | None,
) -> None:
    """Insert a visit feedback row."""
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text(
            "INSERT INTO visit_feedback "
            "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy, free_text) "
            "VALUES (:sid, :submitted_at, :made_it, :outcomes, :accuracy, :free_text)"
        ),
        {
            "sid": session_id,
            "submitted_at": now,
            "made_it": made_it_to_center,
            "outcomes": outcomes_json,
            "accuracy": plan_accuracy,
            "free_text": free_text,
        },
    )
    await db.commit()


async def get_feedback_stats(db: AsyncSession, resource_id: int, window_days: int = 30) -> dict:
    """Aggregate feedback for a resource within a time window."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    result = await db.execute(
        text(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN helpful = 0 THEN 1 ELSE 0 END) as unhelpful "
            "FROM resource_feedback "
            "WHERE resource_id = :rid AND submitted_at > :cutoff"
        ),
        {"rid": resource_id, "cutoff": cutoff},
    )
    row = result.fetchone()
    return {"total": row[0] or 0, "unhelpful_count": row[1] or 0}


async def get_all_feedback_stats(db: AsyncSession, window_days: int = 30) -> list[dict]:
    """Aggregate feedback stats for all resources in a single query."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    result = await db.execute(
        text(
            "SELECT resource_id, COUNT(*) as total, "
            "SUM(CASE WHEN helpful = 0 THEN 1 ELSE 0 END) as unhelpful "
            "FROM resource_feedback "
            "WHERE submitted_at > :cutoff "
            "GROUP BY resource_id"
        ),
        {"cutoff": cutoff},
    )
    return [
        {"resource_id": row[0], "total": row[1] or 0, "unhelpful_count": row[2] or 0}
        for row in result
    ]


async def update_resource_health(
    db: AsyncSession, resource_id: int, status: ResourceHealth,
) -> None:
    """Update health_status for a resource. Caller must commit."""
    await db.execute(
        text("UPDATE resources SET health_status = :status WHERE id = :rid"),
        {"status": status.value, "rid": resource_id},
    )
