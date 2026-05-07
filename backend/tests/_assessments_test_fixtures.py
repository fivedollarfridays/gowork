"""Shared fixtures + helpers for the queries_assessments test suite.

Two test modules consume this:

* ``test_queries_assessments_crud.py`` — the basic CRUD helpers
  (create_assessment, create_draft_version, get_version_with_questions).
* ``test_queries_assessments_state.py`` — state-machine flows
  (list_pending_reviews, record_review, publish_version,
  get_published_version, retire_version).

Splitting the test surface keeps each test file under the per-file
size limit; sharing the fixtures + helpers via this module keeps the
DRY invariant ("the same draft seed is used everywhere"). Filename
starts with an underscore so pytest does not treat it as a test
module.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_assessments
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.assessments_schema import apply_ddl as apply_assessments_ddl


@pytest.fixture
async def assessments_engine(db_engine):
    """``db_engine`` plus accounts + assessments DDL applied on top."""
    async with db_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_assessments_ddl)
    return db_engine


@pytest.fixture
def session_factory(assessments_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        assessments_engine, class_=AsyncSession, expire_on_commit=False
    )


async def make_account(session: AsyncSession, email: str) -> int:
    return await queries_accounts.create_account(session, email=email)


def question(position: int, *, kind: str = "mcq", weight: float = 1.0) -> dict:
    return {
        "position": position,
        "prompt": f"q-{position}",
        "kind": kind,
        "rubric_json": '{"answer": "x"}',
        "scoring_weight": weight,
    }


async def seed_assessment_with_draft(
    session: AsyncSession,
    *,
    slug: str,
    track: str = "vocational",
    question_count: int = 2,
) -> tuple[int, int, int]:
    """Create one account + assessment + draft version, returning ids.

    Returns ``(account_id, assessment_id, version_id)``.
    """
    account_id = await make_account(session, f"{slug}@example.com")
    aid = await queries_assessments.create_assessment(
        session,
        slug=slug,
        kind="skill_probe",
        track=track,
        created_by=account_id,
    )
    questions = [question(i + 1) for i in range(question_count)]
    vid = await queries_assessments.create_draft_version(
        session,
        assessment_id=aid,
        drafted_by=account_id,
        questions=questions,
    )
    return account_id, aid, vid


async def approve_version(
    session: AsyncSession, version_id: int, reviewer_id: int
) -> None:
    """Walk a draft through the approve state-transition."""
    await queries_assessments.record_review(
        session,
        version_id=version_id,
        reviewer_id=reviewer_id,
        action="approve",
        comment="lgtm",
    )


__all__ = [
    "assessments_engine",
    "session_factory",
    "make_account",
    "question",
    "seed_assessment_with_draft",
    "approve_version",
]
