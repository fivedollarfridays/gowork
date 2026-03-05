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


async def get_resources_by_categories(session: AsyncSession, categories: set[str]) -> list[dict]:
    """Fetch resources matching any of the given categories in a single query."""
    if not categories:
        return []
    placeholders = ", ".join(f":c{i}" for i in range(len(categories)))
    params = {f"c{i}": cat for i, cat in enumerate(sorted(categories))}
    result = await session.execute(
        text(f"SELECT * FROM resources WHERE category IN ({placeholders})"),
        params,
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


async def create_session(session: AsyncSession, session_data: dict, session_id: str | None = None) -> str:
    """Insert a new session row with UUID and 24h expiry. Returns session id."""
    session_id = session_id or str(uuid.uuid4())
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    expires = (now_dt + timedelta(hours=24)).isoformat()
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


async def update_session_plan(session: AsyncSession, session_id: str, plan_json: str) -> None:
    """Update the plan column for an existing session."""
    await session.execute(
        text("UPDATE sessions SET plan = :plan WHERE id = :id"),
        {"plan": plan_json, "id": session_id},
    )
    await session.commit()


async def insert_job_listings(session: AsyncSession, listings: list[dict]) -> int:
    """Bulk insert job listings. Returns count inserted."""
    if not listings:
        return 0
    params = [
        {
            "title": row["title"],
            "company": row.get("company"),
            "location": row.get("location"),
            "description": row.get("description"),
            "url": row.get("url"),
            "source": row.get("source"),
            "scraped_at": row["scraped_at"],
            "expires_at": row.get("expires_at"),
        }
        for row in listings
    ]
    await session.execute(
        text(
            "INSERT INTO job_listings (title, company, location, description, url, source, scraped_at, expires_at) "
            "VALUES (:title, :company, :location, :description, :url, :source, :scraped_at, :expires_at)"
        ),
        params,
    )
    await session.commit()
    return len(listings)


async def get_job_listings_by_source(session: AsyncSession, source: str) -> list[dict]:
    """Fetch job listings filtered by source."""
    result = await session.execute(
        text("SELECT * FROM job_listings WHERE source = :source"),
        {"source": source},
    )
    return [dict(row._mapping) for row in result]
