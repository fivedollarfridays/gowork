"""End-to-end resume matching against real Fort Worth seed data.

These tests prove the demo headline contract:
  * a nurse resume + ZIP 76102 returns healthcare jobs at the top
  * a forklift resume + ZIP 76102 returns warehouse jobs at the top
  * scores VARY across jobs (no more "0.363 for everyone")
  * empty resume falls back gracefully without crashing
  * different resumes against the same ZIP produce different rankings
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.cities.config import set_city_context, clear_city_context
from app.modules.matching.engine import generate_plan
from app.modules.matching.relevance_scorer import build_resume_profile
from app.modules.matching.types import (
    AvailableHours,
    BarrierType,
    EmploymentStatus,
    UserProfile,
    determine_severity,
)


NURSE_RESUME = (
    "Registered Nurse with 10 years of ICU experience. BSN, BLS, ACLS "
    "certified. Epic EHR. Cared for post-op critical care patients. "
    "Worked at hospital trauma units."
)

FORKLIFT_RESUME = (
    "Forklift operator with 5 years warehouse experience. OSHA-10. "
    "Loaded and unloaded freight, sit-down forklift, reach truck. "
    "Pallet jack, inventory, picker and packer."
)

ADMIN_RESUME = (
    "Customer service representative with 3 years experience in call "
    "center and front desk reception. Office, data entry, scheduling. "
    "High school graduate."
)

WELDER_RESUME = (
    "Welder with 7 years MIG and TIG welding experience on commercial "
    "construction sites. OSHA-30. Aerospace welding, AS9100 awareness. "
    "Construction laborer background."
)


def _profile_for(zip_code: str = "76102") -> UserProfile:
    return UserProfile(
        session_id="test-session",
        zip_code=zip_code,
        employment_status=EmploymentStatus.UNEMPLOYED,
        barrier_count=0,
        primary_barriers=[],
        barrier_severity=determine_severity(0),
        needs_credit_assessment=False,
        transit_dependent=False,
        schedule_type=AvailableHours.FLEXIBLE,
        work_history="",
        target_industries=[],
    )


async def _bootstrap_db():
    """Create a fresh DB seeded with FW jobs."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_url = f"sqlite+aiosqlite:///{path}"

    from app.core.database import init_db
    from app.integrations.honestjobs.seed import seed_honestjobs_listings

    engine = create_async_engine(db_url, echo=False)
    await init_db(engine)
    sm = async_sessionmaker(engine, expire_on_commit=False)
    async with sm() as session:
        await seed_honestjobs_listings(session)
        await session.commit()
    return engine, sm, path


@pytest.mark.asyncio
async def test_nurse_resume_top_match_is_healthcare():
    """A nurse resume in 76102 should rank healthcare jobs at the top."""
    engine, sm, path = await _bootstrap_db()
    try:
        set_city_context("fort-worth")
        async with sm() as session:
            plan = await generate_plan(
                _profile_for("76102"), session, resume_text=NURSE_RESUME,
            )
        clear_city_context()

        top_jobs = list(plan.strong_matches)[:5]
        assert top_jobs, "no strong matches returned"
        # At least one of the top 5 should be a healthcare-tagged role.
        top_text = " ".join(
            f"{j.title} {j.company or ''}".lower() for j in top_jobs
        )
        assert any(kw in top_text for kw in (
            "nurse", "patient", "pharmacy", "phlebot", "medical",
            "dietary", "hospital", "jps", "cook children",
            "baylor", "methodist",
        )), f"no healthcare in top 5: {[j.title for j in top_jobs]}"

        # And the very top job should mention a resume signal in match_reason.
        assert plan.strong_matches[0].match_reason
        assert plan.strong_matches[0].match_reason != "Entry-level opportunity"
    finally:
        await engine.dispose()
        os.unlink(path)


@pytest.mark.asyncio
async def test_forklift_resume_top_match_is_warehouse():
    """A forklift resume in 76102 should rank warehouse/logistics jobs at the top."""
    engine, sm, path = await _bootstrap_db()
    try:
        set_city_context("fort-worth")
        async with sm() as session:
            plan = await generate_plan(
                _profile_for("76102"), session, resume_text=FORKLIFT_RESUME,
            )
        clear_city_context()

        top_jobs = list(plan.strong_matches)[:5]
        assert top_jobs, "no strong matches returned"
        top_text = " ".join(
            f"{j.title} {j.company or ''}".lower() for j in top_jobs
        )
        assert any(kw in top_text for kw in (
            "warehouse", "forklift", "picker", "packer", "stocker",
            "yard", "hillwood", "amazon", "fedex", "ups",
            "goodwill", "walmart", "bnsf",
        )), f"no warehouse in top 5: {[j.title for j in top_jobs]}"
    finally:
        await engine.dispose()
        os.unlink(path)


@pytest.mark.asyncio
async def test_scores_vary_across_jobs_for_same_resume():
    """A nurse resume should produce VARIED scores — no more 0.363 for everyone."""
    engine, sm, path = await _bootstrap_db()
    try:
        set_city_context("fort-worth")
        async with sm() as session:
            plan = await generate_plan(
                _profile_for("76102"), session, resume_text=NURSE_RESUME,
            )
        clear_city_context()

        all_jobs = list(plan.strong_matches) + list(plan.after_repair)
        assert len(all_jobs) >= 10, "need enough jobs to verify variance"

        scores = [round(j.relevance_score, 3) for j in all_jobs]
        unique_scores = set(scores)
        # Pre-fix the demo had all jobs at 0.363.  After fix we expect
        # at LEAST 5 unique scores across the 60+ FW listings.
        assert len(unique_scores) >= 5, (
            f"only {len(unique_scores)} unique scores: {sorted(unique_scores)}"
        )

        # Top score should be meaningfully higher than median.
        top = max(scores)
        median = sorted(scores)[len(scores) // 2]
        assert top > median, f"top {top} not above median {median}"
    finally:
        await engine.dispose()
        os.unlink(path)


@pytest.mark.asyncio
async def test_two_resumes_produce_different_top_matches():
    """A nurse vs a forklift resume should rank jobs DIFFERENTLY."""
    engine, sm, path = await _bootstrap_db()
    try:
        set_city_context("fort-worth")
        async with sm() as session:
            nurse_plan = await generate_plan(
                _profile_for("76102"), session, resume_text=NURSE_RESUME,
            )
            forklift_plan = await generate_plan(
                _profile_for("76102"), session, resume_text=FORKLIFT_RESUME,
            )
        clear_city_context()

        nurse_top = [j.title for j in list(nurse_plan.strong_matches)[:5]]
        forklift_top = [j.title for j in list(forklift_plan.strong_matches)[:5]]

        # The two top-5 lists should not be identical.
        assert nurse_top != forklift_top, (
            f"identical top-5 for both resumes: {nurse_top}"
        )
    finally:
        await engine.dispose()
        os.unlink(path)


@pytest.mark.asyncio
async def test_empty_resume_falls_back_without_crashing():
    """No resume should still produce a coherent plan."""
    engine, sm, path = await _bootstrap_db()
    try:
        set_city_context("fort-worth")
        async with sm() as session:
            plan = await generate_plan(
                _profile_for("76102"), session, resume_text="",
            )
        clear_city_context()
        assert plan is not None
        # We expect at least one job match to come back with valid score.
        all_jobs = list(plan.strong_matches) + list(plan.after_repair)
        assert all_jobs
        for j in all_jobs:
            assert 0.0 <= j.relevance_score <= 1.0
    finally:
        await engine.dispose()
        os.unlink(path)


@pytest.mark.asyncio
async def test_city_correct_jobs_for_each_zip():
    """Same resume against AL ZIP vs TX ZIP returns city-correct jobs."""
    engine, sm, path = await _bootstrap_db()
    try:
        # Fort Worth
        set_city_context("fort-worth")
        async with sm() as session:
            tx_plan = await generate_plan(
                _profile_for("76102"), session, resume_text=NURSE_RESUME,
            )
        clear_city_context()

        # Montgomery
        set_city_context("montgomery")
        async with sm() as session:
            al_plan = await generate_plan(
                _profile_for("36104"), session, resume_text=NURSE_RESUME,
            )
        clear_city_context()

        tx_locations = [j.location or "" for j in tx_plan.strong_matches]
        al_locations = [j.location or "" for j in al_plan.strong_matches]

        # No cross-contamination either direction.
        assert all(", TX" in loc for loc in tx_locations), (
            f"non-TX leaked: {tx_locations}"
        )
        assert all(", AL" in loc for loc in al_locations), (
            f"non-AL leaked: {al_locations}"
        )
    finally:
        await engine.dispose()
        os.unlink(path)
