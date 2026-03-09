"""Async query helpers for SQLite database."""

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.criminal.record_profile import RecordProfile


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


async def get_all_transit_stops(session: AsyncSession) -> list[dict]:
    """Fetch transit stop coordinates for distance scoring.

    Returns only lat/lng (the fields used by _compute_stop_distances in engine.py).
    NULL coordinates are filtered at the SQL level for efficiency.
    """
    result = await session.execute(
        text("SELECT lat, lng FROM transit_stops WHERE lat IS NOT NULL AND lng IS NOT NULL"),
    )
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
            "qualifications, plan, profile, expires_at) "
            "VALUES (:id, :created_at, :barriers, :credit_profile, "
            ":qualifications, :plan, :profile, :expires_at)"
        ),
        {
            "id": session_id,
            "created_at": now,
            "barriers": session_data["barriers"],
            "credit_profile": session_data.get("credit_profile"),
            "qualifications": session_data.get("qualifications"),
            "plan": session_data.get("plan"),
            "profile": session_data.get("profile"),
            "expires_at": expires,
        },
    )
    await session.commit()
    return session_id


async def get_session_by_id(session: AsyncSession, session_id: str) -> dict | None:
    """Fetch a session by id, returning None if expired."""
    now = datetime.now(timezone.utc).isoformat()
    result = await session.execute(
        text(
            "SELECT * FROM sessions WHERE id = :id "
            "AND (expires_at IS NULL OR expires_at > :now)"
        ),
        {"id": session_id, "now": now},
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


async def insert_record_profile(
    session: AsyncSession, session_id: str, profile: RecordProfile,
) -> None:
    """Insert or replace a criminal record profile for a session."""
    await session.execute(
        text(
            "INSERT OR REPLACE INTO record_profiles "
            "(session_id, record_types, charge_categories, "
            "years_since_conviction, completed_sentence) "
            "VALUES (:sid, :rt, :cc, :ysc, :cs)"
        ),
        {
            "sid": session_id,
            "rt": json.dumps([t.value for t in profile.record_types]),
            "cc": json.dumps([c.value for c in profile.charge_categories]),
            "ysc": profile.years_since_conviction,
            "cs": 1 if profile.completed_sentence else 0,
        },
    )
    await session.commit()


async def get_record_profile(
    session: AsyncSession, session_id: str,
) -> RecordProfile | None:
    """Fetch a criminal record profile by session_id, or None."""
    result = await session.execute(
        text("SELECT * FROM record_profiles WHERE session_id = :sid"),
        {"sid": session_id},
    )
    row = result.first()
    if row is None:
        return None
    data = dict(row._mapping)
    return RecordProfile(
        record_types=json.loads(data["record_types"]),
        charge_categories=json.loads(data["charge_categories"]),
        years_since_conviction=data["years_since_conviction"],
        completed_sentence=bool(data["completed_sentence"]),
    )
