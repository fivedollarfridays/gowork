"""Async query helpers for SQLite database."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_all_resources(session: AsyncSession) -> list[dict]:
    """Fetch all resources."""
    result = await session.execute(text("SELECT * FROM resources"))
    return [dict(row._mapping) for row in result]


async def get_resource_by_id(session: AsyncSession, resource_id: int) -> dict | None:
    """Fetch a single resource by id."""
    result = await session.execute(
        text("SELECT * FROM resources WHERE id = :id"),
        {"id": resource_id},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_resources_by_category(session: AsyncSession, category: str) -> list[dict]:
    """Fetch resources filtered by category."""
    result = await session.execute(
        text("SELECT * FROM resources WHERE category = :category"),
        {"category": category},
    )
    return [dict(row._mapping) for row in result]


async def get_all_transit_routes(session: AsyncSession) -> list[dict]:
    """Fetch all transit routes."""
    result = await session.execute(text("SELECT * FROM transit_routes"))
    return [dict(row._mapping) for row in result]


async def get_all_employers(session: AsyncSession) -> list[dict]:
    """Fetch all employers."""
    result = await session.execute(text("SELECT * FROM employers"))
    return [dict(row._mapping) for row in result]


async def create_session(session: AsyncSession, session_data: dict) -> str:
    """Insert a new session row with UUID and 24h expiry. Returns session id."""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    await session.execute(
        text(
            "INSERT INTO sessions (id, created_at, barriers, credit_profile, "
            "qualifications, plan, expires_at) "
            "VALUES (:id, :created_at, :barriers, :credit_profile, "
            ":qualifications, :plan, :expires_at)"
        ),
        {
            "id": session_id,
            "created_at": now,
            "barriers": session_data["barriers"],
            "credit_profile": session_data.get("credit_profile"),
            "qualifications": session_data.get("qualifications"),
            "plan": session_data.get("plan"),
            "expires_at": expires,
        },
    )
    await session.commit()
    return session_id


async def get_all_job_listings(session: AsyncSession) -> list[dict]:
    """Fetch all job listings."""
    result = await session.execute(text("SELECT * FROM job_listings"))
    return [dict(row._mapping) for row in result]


async def get_job_listing_by_id(session: AsyncSession, job_id: int) -> dict | None:
    """Fetch a single job listing by id."""
    result = await session.execute(
        text("SELECT * FROM job_listings WHERE id = :id"),
        {"id": job_id},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_session_by_id(session: AsyncSession, session_id: str) -> dict | None:
    """Fetch a session by id."""
    result = await session.execute(
        text("SELECT * FROM sessions WHERE id = :id"),
        {"id": session_id},
    )
    row = result.first()
    return dict(row._mapping) if row else None
