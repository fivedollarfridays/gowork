"""Tests for outcome intelligence DB queries.

These tests exercise the async query layer that reads visit_feedback
and sessions data to produce barrier resolution observations.
"""

import json

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session_factory
from app.modules.outcomes.intelligence_queries import (
    get_barrier_feedback_rows,
)


@pytest.fixture
async def db(test_engine):
    """Provide a DB session for testing."""
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


async def _insert_session(db: AsyncSession, sid: str, barriers: list[str]) -> None:
    """Insert a test session with barriers."""
    await db.execute(
        text(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (:id, '2026-01-01T00:00:00', :barriers, '2027-01-01T00:00:00')"
        ),
        {"id": sid, "barriers": json.dumps(barriers)},
    )
    await db.commit()


async def _insert_visit_feedback(
    db: AsyncSession, sid: str, outcomes: list[str], plan_accuracy: int,
) -> None:
    """Insert a test visit_feedback row."""
    await db.execute(
        text(
            "INSERT INTO visit_feedback "
            "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy) "
            "VALUES (:sid, '2026-03-01T00:00:00', 1, :outcomes, :accuracy)"
        ),
        {"sid": sid, "outcomes": json.dumps(outcomes), "accuracy": plan_accuracy},
    )
    await db.commit()


class TestGetBarrierFeedbackRows:
    """DB query returns flattened barrier feedback observations."""

    @pytest.mark.anyio
    async def test_returns_empty_for_no_feedback(self, db):
        rows = await get_barrier_feedback_rows(db)
        assert rows == []

    @pytest.mark.anyio
    async def test_returns_barriers_from_session_with_feedback(self, db):
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await _insert_session(db, sid, ["criminal_record", "credit"])
        await _insert_visit_feedback(db, sid, ["got_a_job"], 3)
        rows = await get_barrier_feedback_rows(db)
        assert len(rows) == 2
        barrier_ids = {r["barrier_id"] for r in rows}
        assert barrier_ids == {"criminal_record", "credit"}

    @pytest.mark.anyio
    async def test_skips_sessions_without_feedback(self, db):
        sid1 = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        sid2 = "aaaaaaaa-bbbb-cccc-dddd-000000000002"
        await _insert_session(db, sid1, ["criminal_record"])
        await _insert_session(db, sid2, ["credit"])
        # Only sid1 has feedback
        await _insert_visit_feedback(db, sid1, [], 3)
        rows = await get_barrier_feedback_rows(db)
        assert len(rows) == 1
        assert rows[0]["barrier_id"] == "criminal_record"

    @pytest.mark.anyio
    async def test_includes_plan_accuracy(self, db):
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await _insert_session(db, sid, ["transportation"])
        await _insert_visit_feedback(db, sid, ["resolved_barrier"], 5)
        rows = await get_barrier_feedback_rows(db)
        assert rows[0]["plan_accuracy"] == 5

    @pytest.mark.anyio
    async def test_marks_resolved_from_outcomes(self, db):
        """Barriers mentioned in outcomes are marked resolved."""
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await _insert_session(db, sid, ["criminal_record", "credit"])
        await _insert_visit_feedback(db, sid, ["criminal_record"], 3)
        rows = await get_barrier_feedback_rows(db)
        cr = next(r for r in rows if r["barrier_id"] == "criminal_record")
        credit = next(r for r in rows if r["barrier_id"] == "credit")
        assert cr["resolved"] is True
        assert credit["resolved"] is False

    @pytest.mark.anyio
    async def test_handles_malformed_barriers_json(self, db):
        """Malformed barriers JSON is skipped gracefully."""
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES (:id, '2026-01-01', 'NOT-JSON', '2027-01-01')"
            ),
            {"id": sid},
        )
        await db.commit()
        await _insert_visit_feedback(db, sid, [], 3)
        rows = await get_barrier_feedback_rows(db)
        assert rows == []

    @pytest.mark.anyio
    async def test_handles_null_outcomes(self, db):
        """NULL outcomes means no barriers are marked resolved."""
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await _insert_session(db, sid, ["credit"])
        await db.execute(
            text(
                "INSERT INTO visit_feedback "
                "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy) "
                "VALUES (:sid, '2026-03-01', 1, NULL, 3)"
            ),
            {"sid": sid},
        )
        await db.commit()
        rows = await get_barrier_feedback_rows(db)
        assert len(rows) == 1
        assert rows[0]["resolved"] is False
