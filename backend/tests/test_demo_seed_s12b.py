"""Tests for S12b T12.34 — demo seed extension + sessions.demo column.

Cycle 1: m005 adds sessions.demo column (default FALSE) + round-trip downgrade.
Cycle 2: Worker-companion seed creates 5 sessions per city, all demo=1.
Cycle 3: Every seeded session represents one stall state (none/soft/medium/
         hard/breakthrough) with computed-state verification.
Cycle 4: Every session has appointment + application + resume + snapshot +
         outcomes_records tagged with its city.
Cycle 5: Seed is idempotent on re-run.
Cycle 6: Community funnel (T12.12) excludes demo=1 sessions (regression).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core.migrations import m001_initial, m002_s12_worker_companion
from app.core.migrations import m005_sessions_demo_column as m005
from app.demo_seed import seed_worker_companion_sessions
from app.modules.common.temporal_types import StallLevel
from app.modules.engagement.stall_detector import compute_stall_for_session
from app.modules.jobs.funnel_analytics import (
    FunnelResult,
    compute_community_funnel,
)
from app.modules.plan._plan_refresher_db import detect_breakthrough


CITIES = ("montgomery", "fort-worth")
EXPECTED_STATES = ("none", "soft", "medium", "hard", "breakthrough")
SESSIONS_PER_CITY = 5


# -------------------- Fixtures --------------------


def _fresh_db(tmp_path: Path, name: str = "s12b.db") -> str:
    """Create a DB with m001 + m002 applied — baseline before m005."""
    db_path = str(tmp_path / name)
    conn = sqlite3.connect(db_path)
    try:
        m001_initial.upgrade(conn)
        m002_s12_worker_companion.upgrade(conn)
        conn.commit()
    finally:
        conn.close()
    return db_path


def _apply_m005(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        m005.upgrade(conn)
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = _fresh_db(tmp_path)
    _apply_m005(path)
    return path


# -------------------- Cycle 1: migration m005 --------------------


def test_m005_adds_demo_column(tmp_path: Path) -> None:
    """m005.upgrade adds sessions.demo with default FALSE (0)."""
    path = _fresh_db(tmp_path)
    _apply_m005(path)

    conn = sqlite3.connect(path)
    try:
        cols = {r[1]: r for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
    finally:
        conn.close()

    assert "demo" in cols
    # PRAGMA table_info row: (cid, name, type, notnull, dflt_value, pk)
    assert cols["demo"][4] in ("0", "FALSE", "false")


def test_m005_existing_rows_default_to_false(tmp_path: Path) -> None:
    """Pre-existing sessions get demo=0 from the DEFAULT FALSE column."""
    path = _fresh_db(tmp_path)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, '[]', ?)",
            ("legacy-001", "2026-01-01T00:00:00+00:00", "2027-01-01T00:00:00+00:00"),
        )
        conn.commit()
    finally:
        conn.close()

    _apply_m005(path)

    conn = sqlite3.connect(path)
    try:
        row = conn.execute(
            "SELECT demo FROM sessions WHERE id = 'legacy-001'"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[0] == 0


def test_m005_downgrade_drops_column(tmp_path: Path) -> None:
    """m005.downgrade removes the sessions.demo column (round-trip clean)."""
    path = _fresh_db(tmp_path)
    _apply_m005(path)

    conn = sqlite3.connect(path)
    try:
        m005.downgrade(conn)
        conn.commit()
        cols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
    finally:
        conn.close()
    assert "demo" not in cols


def test_m005_upgrade_idempotent(tmp_path: Path) -> None:
    """Re-applying m005 on a DB that already has the column is a no-op."""
    path = _fresh_db(tmp_path)
    _apply_m005(path)
    # Second application must not raise.
    _apply_m005(path)

    conn = sqlite3.connect(path)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
    finally:
        conn.close()
    assert "demo" in cols


# -------------------- Cycle 2: seed shape + demo flag --------------------


def test_seed_creates_five_sessions_per_city(db_path: str) -> None:
    """Seed adds 5 sessions for each of the two cities (10 total)."""
    summary = seed_worker_companion_sessions(db_path=db_path)

    assert summary["sessions_created"] == SESSIONS_PER_CITY * len(CITIES)

    conn = sqlite3.connect(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    finally:
        conn.close()
    assert total == SESSIONS_PER_CITY * len(CITIES)


def test_all_seeded_sessions_have_demo_flag(db_path: str) -> None:
    """Every seeded session has demo=1 (filterable from analytics views)."""
    seed_worker_companion_sessions(db_path=db_path)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT demo FROM sessions").fetchall()
    finally:
        conn.close()
    assert len(rows) > 0
    assert all(r[0] == 1 for r in rows)


def test_seed_tags_city_via_outcomes_records(db_path: str) -> None:
    """Each session has at least one outcomes_records row tagged with its city.

    Required for T12.12's `city_scoped_session_ids` to pick it up.
    """
    seed_worker_companion_sessions(db_path=db_path)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT session_id, payload_json FROM outcomes_records"
        ).fetchall()
    finally:
        conn.close()

    cities_by_session: dict[str, set[str]] = {}
    for sid, payload in rows:
        parsed = json.loads(payload) if payload else {}
        city = parsed.get("city")
        if city:
            cities_by_session.setdefault(sid, set()).add(city)

    assert len(cities_by_session) == SESSIONS_PER_CITY * len(CITIES)
    tagged_cities = {c for cs in cities_by_session.values() for c in cs}
    assert tagged_cities == set(CITIES)


# -------------------- Cycle 3: stall state coverage --------------------


def test_all_five_stall_states_represented_per_city(db_path: str) -> None:
    """Each city has exactly one session per expected stall state label."""
    seed_worker_companion_sessions(db_path=db_path)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, profile FROM sessions"
        ).fetchall()
    finally:
        conn.close()

    per_city: dict[str, set[str]] = {}
    for sid, profile in rows:
        prof = json.loads(profile) if profile else {}
        city = prof.get("city")
        state = prof.get("demo_stall_state")
        assert city in CITIES, f"unknown city for {sid}: {city}"
        assert state in EXPECTED_STATES, f"unknown state for {sid}: {state}"
        per_city.setdefault(city, set()).add(state)

    for city in CITIES:
        assert per_city[city] == set(EXPECTED_STATES), (
            f"city {city} missing states: {set(EXPECTED_STATES) - per_city[city]}"
        )


def test_stall_detector_classifies_seeded_sessions(db_path: str) -> None:
    """compute_stall_for_session returns the label the seed intends.

    - `none` → StallLevel.NONE (recent progress)
    - `soft` → StallLevel.SOFT (3-6 days)
    - `medium` → StallLevel.MEDIUM (7-13 days)
    - `hard` → StallLevel.HARD (≥14 days)
    - `breakthrough` → any stall level + recent barrier_resolved outcome
    """
    seed_worker_companion_sessions(db_path=db_path)
    now = datetime.now(timezone.utc)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, profile FROM sessions"
        ).fetchall()
    finally:
        conn.close()

    state_to_level = {
        "none": StallLevel.NONE,
        "soft": StallLevel.SOFT,
        "medium": StallLevel.MEDIUM,
        "hard": StallLevel.HARD,
    }
    for sid, profile in rows:
        prof = json.loads(profile)
        state = prof["demo_stall_state"]
        if state == "breakthrough":
            event = detect_breakthrough(sid, db_path=db_path, now=now)
            assert event is not None, f"breakthrough seed {sid} missing outcome"
        else:
            result = compute_stall_for_session(sid, db_path=db_path, now=now)
            assert result.stall_level == state_to_level[state], (
                f"session {sid} expected {state} got {result.stall_level}"
            )


# -------------------- Cycle 4: supporting rows present --------------------


def test_every_session_has_appointment_application_resume_snapshot(
    db_path: str,
) -> None:
    """Each seeded session has ≥1 row in each support table."""
    seed_worker_companion_sessions(db_path=db_path)

    conn = sqlite3.connect(db_path)
    try:
        session_ids = [r[0] for r in conn.execute("SELECT id FROM sessions").fetchall()]
        for sid in session_ids:
            for table in (
                "appointments",
                "job_applications",
                "resume_versions",
                "daily_progress_snapshots",
            ):
                n = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE session_id = ?",
                    (sid,),
                ).fetchone()[0]
                assert n >= 1, f"{table} missing row for {sid}"
    finally:
        conn.close()


# -------------------- Cycle 5: idempotent --------------------


def test_seed_is_idempotent(db_path: str) -> None:
    """Running the seed twice leaves the same row counts — no dup sessions."""
    seed_worker_companion_sessions(db_path=db_path)
    seed_worker_companion_sessions(db_path=db_path)

    conn = sqlite3.connect(db_path)
    try:
        sess = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        appts = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    finally:
        conn.close()
    assert sess == SESSIONS_PER_CITY * len(CITIES)
    assert appts >= SESSIONS_PER_CITY * len(CITIES)
    # At most one appointment per session expected by the seed design
    assert appts == SESSIONS_PER_CITY * len(CITIES)


# -------------------- Cycle 6: T12.12 regression --------------------


def test_community_funnel_excludes_seeded_demo_sessions(db_path: str) -> None:
    """Demo-seeded sessions do NOT contribute to /api/intelligence funnel."""
    seed_worker_companion_sessions(db_path=db_path)

    for city in CITIES:
        result = compute_community_funnel(city, db_path=db_path)
        cell = result["__all__"]
        # Empty-DB case returns FunnelResult with zero counts (no PII risk).
        # Demo-only DB should look empty to the funnel.
        assert isinstance(cell, FunnelResult)
        counts = cell.counts
        total = (
            counts.draft + counts.applied + counts.interview
            + counts.offer + counts.rejected + counts.withdrawn
        )
        assert total == 0, (
            f"city={city} demo sessions leaked into funnel: {counts}"
        )
