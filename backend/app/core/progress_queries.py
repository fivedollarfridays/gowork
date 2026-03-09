"""Query helpers for action plan progress tracking."""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_action_checklist(session: AsyncSession, session_id: str) -> dict:
    """Fetch the action checklist for a session, defaulting to empty dict."""
    result = await session.execute(
        text("SELECT action_checklist FROM sessions WHERE id = :id"),
        {"id": session_id},
    )
    row = result.first()
    if not row or not row[0]:
        return {}
    return json.loads(row[0])


async def update_action_checklist(
    session: AsyncSession, session_id: str, checklist: dict,
) -> None:
    """Update the action checklist JSON for a session."""
    await session.execute(
        text("UPDATE sessions SET action_checklist = :cl WHERE id = :id"),
        {"cl": json.dumps(checklist), "id": session_id},
    )
    await session.commit()


async def store_previous_plan(session: AsyncSession, session_id: str) -> None:
    """Copy the current plan into previous_plan before a refresh."""
    await session.execute(
        text("UPDATE sessions SET previous_plan = plan WHERE id = :id"),
        {"id": session_id},
    )
    await session.commit()
