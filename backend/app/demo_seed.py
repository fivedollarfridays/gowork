"""Demo seed data — realistic Fort Worth sessions and feedback.

Populates the database with 50 Fort Worth sessions with varied
barrier profiles and 30 visit_feedback entries with resolution
outcomes. Designed for the HackFW 2026 demo so the N+1 intelligence
engine has data to calibrate from.

Run as: py -3.12 -m app.demo_seed
Or call run_demo_seed(db) from code.

Uses random.Random(42) for deterministic, reproducible output.
"""

import json
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Fort Worth ZIP codes
_FW_ZIPS = [
    "76102", "76103", "76104", "76105", "76106",
    "76107", "76108", "76109", "76110", "76111",
    "76112", "76113", "76114", "76115", "76116",
    "76117", "76118", "76119",
]

# Barrier probabilities matching Fort Worth demographics
_BARRIER_PROBS: dict[str, float] = {
    "criminal_record": 0.40,
    "transportation": 0.60,
    "childcare": 0.35,
    "credit": 0.50,
    "housing": 0.25,
    "health": 0.15,
    "training": 0.20,
}

# Realistic resolution time ranges (weeks) per barrier
_RESOLUTION_RANGES: dict[str, tuple[int, int]] = {
    "criminal_record": (6, 16),
    "credit": (4, 12),
    "transportation": (1, 4),
    "childcare": (3, 8),
    "housing": (4, 10),
    "health": (2, 6),
    "training": (6, 14),
}

_EMPLOYMENT_STATUSES = ["unemployed", "part_time", "gig", "seeking"]
_SESSION_COUNT = 50
_FEEDBACK_COUNT = 30


def _generate_session_id(rng: random.Random) -> str:
    """Generate a deterministic UUID from the seeded RNG."""
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def _pick_barriers(rng: random.Random) -> list[str]:
    """Pick barriers for a session based on Fort Worth probabilities."""
    barriers = [
        bid for bid, prob in _BARRIER_PROBS.items()
        if rng.random() < prob
    ]
    if not barriers:
        barriers = [rng.choice(list(_BARRIER_PROBS.keys()))]
    return barriers


def _build_profile(rng: random.Random, barriers: list[str]) -> dict:
    """Build a realistic Fort Worth user profile."""
    return {
        "zip_code": rng.choice(_FW_ZIPS),
        "employment_status": rng.choice(_EMPLOYMENT_STATUSES),
        "barrier_count": len(barriers),
        "primary_barriers": barriers,
    }


def _build_plan(session_id: str, barriers: list[str]) -> dict:
    """Build a minimal plan JSON for the session."""
    return {
        "plan_id": f"demo-{session_id[:8]}",
        "session_id": session_id,
        "barriers": [{"type": b} for b in barriers],
        "immediate_next_steps": [
            "Visit Workforce Solutions Tarrant County",
            "Complete online assessment",
        ],
    }


def _build_benefits_profile(rng: random.Random) -> dict:
    """Build a realistic Texas benefits profile."""
    programs = ["SNAP", "TANF", "Medicaid", "CHIP", "CEAP", "Childcare_Subsidy"]
    enrolled = [p for p in programs if rng.random() < 0.3]
    return {
        "household_size": rng.randint(1, 5),
        "current_monthly_income": round(rng.uniform(800, 3000), 2),
        "enrolled_programs": enrolled,
        "dependents_under_6": rng.randint(0, 2),
        "dependents_6_to_17": rng.randint(0, 3),
        "state": "TX",
    }


async def _insert_session(
    db: AsyncSession, rng: random.Random, index: int,
) -> tuple[str, list[str]]:
    """Insert one session with profile, plan, and feedback token."""
    sid = _generate_session_id(rng)
    barriers = _pick_barriers(rng)
    profile = _build_profile(rng, barriers)
    plan = _build_plan(sid, barriers)
    bp = _build_benefits_profile(rng)

    now = datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 60))
    exp = (now + timedelta(days=90)).isoformat()

    await db.execute(
        text(
            "INSERT INTO sessions "
            "(id, created_at, barriers, plan, profile, benefits_profile, expires_at) "
            "VALUES (:id, :ts, :b, :p, :prof, :bp, :exp)"
        ),
        {
            "id": sid,
            "ts": now.isoformat(),
            "b": json.dumps(barriers),
            "p": json.dumps(plan),
            "prof": json.dumps(profile),
            "bp": json.dumps(bp),
            "exp": exp,
        },
    )

    # Insert feedback token
    tok = _generate_session_id(rng)
    await db.execute(
        text(
            "INSERT INTO feedback_tokens "
            "(token, session_id, created_at, expires_at) "
            "VALUES (:tok, :sid, :ts, :exp)"
        ),
        {"tok": tok, "sid": sid, "ts": now.isoformat(), "exp": exp},
    )

    return sid, barriers


async def _insert_feedback(
    db: AsyncSession,
    rng: random.Random,
    session_id: str,
    barriers: list[str],
) -> None:
    """Insert one visit_feedback entry with resolution outcomes."""
    # Determine which barriers were resolved
    resolved = [b for b in barriers if rng.random() < 0.6]
    outcomes = json.dumps(resolved)

    # Build per-barrier resolution details for outcomes column
    accuracy = rng.randint(2, 5)
    made_it = 1 if rng.random() < 0.85 else 0
    submitted = datetime.now(timezone.utc) - timedelta(days=rng.randint(0, 30))

    free_text_options = [
        "The career center was very helpful",
        "I got connected with resources I didn't know about",
        "Still working on my criminal record clearance",
        "Transportation is my biggest challenge",
        "Need more help with childcare options",
        None,
    ]

    await db.execute(
        text(
            "INSERT INTO visit_feedback "
            "(session_id, submitted_at, made_it_to_center, outcomes, "
            "plan_accuracy, free_text) "
            "VALUES (:sid, :ts, :made, :outcomes, :acc, :txt)"
        ),
        {
            "sid": session_id,
            "ts": submitted.isoformat(),
            "made": made_it,
            "outcomes": outcomes,
            "acc": accuracy,
            "txt": rng.choice(free_text_options),
        },
    )


async def run_demo_seed(db: AsyncSession) -> dict:
    """Seed realistic Fort Worth demo data into the database.

    Creates 50 sessions with varied barriers matching Fort Worth
    demographics and 30 visit_feedback entries with resolution outcomes.

    Returns summary dict with counts for verification.
    """
    rng = random.Random(42)

    # Create sessions
    sessions: list[tuple[str, list[str]]] = []
    for i in range(_SESSION_COUNT):
        sid, barriers = await _insert_session(db, rng, i)
        sessions.append((sid, barriers))

    # Create feedback for first 30 sessions
    for sid, barriers in sessions[:_FEEDBACK_COUNT]:
        await _insert_feedback(db, rng, sid, barriers)

    await db.commit()

    return {
        "sessions_created": _SESSION_COUNT,
        "feedback_created": _FEEDBACK_COUNT,
    }


async def main() -> None:
    """CLI entry point: py -3.12 -m app.demo_seed."""
    import asyncio

    from app.core.database import get_async_session_factory, get_engine, init_db

    engine = get_engine()
    await init_db(engine)
    factory = get_async_session_factory()

    async with factory() as db:
        result = await run_demo_seed(db)

    print(f"Demo seed complete: {result}")
    await engine.dispose()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
