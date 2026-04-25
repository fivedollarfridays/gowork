"""Tests for S13 T13.3 — QC Reset CLI (`scripts/qc_reset.py`).

Cycles:

- Cycle 1: ``main()`` wipes demo sessions and (when ``reseed=True``) the
  T13.2 seed factory replants them; returns a structured summary.
- Cycle 2: Cascade coverage — every demo-scoped child table reports 0
  rows for the demo session ids after the wipe phase.
- Cycle 3: Idempotency — running ``main()`` twice on a populated DB
  produces a consistent (reset + reseeded) end state.
- Cycle 4: Non-demo sentinel — a manually inserted non-demo session +
  child rows survive the reset untouched.
- Cycle 5: Determinism — seed → reset+reseed → snapshot is identical.
- Cycle 6: Speed budget — full reset on a populated demo DB completes
  in under 5 seconds.
- Cycle 7: CLI — argparse layer accepts ``--db-path`` and ``--no-reseed``.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.demo_seed import seed_worker_companion_sessions
from tests._demo_seed_qc_helpers import (
    apply_m005,
    apply_through_m007,
    fresh_db,
    qc_seed_snapshot,
)

# Importing the CLI module under test. ``scripts/`` lives at repo root and
# the script does its own sys.path bootstrap so this import works from a
# pytest run launched out of ``backend/``.
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import qc_reset  # noqa: E402  (path bootstrap above)


# -------------------- shared fixtures --------------------


@pytest.fixture
def reset_db_path(tmp_path: Path) -> str:
    """DB with all migrations applied — baseline for reset tests."""
    path = fresh_db(tmp_path, name="qc_reset.db")
    apply_m005(path)
    apply_through_m007(path)
    return path


@pytest.fixture
def seeded_db_path(reset_db_path: str) -> str:
    """DB seeded once with the T13.2 demo factory."""
    seed_worker_companion_sessions(db_path=reset_db_path)
    return reset_db_path


# Tables expected to be empty (for demo sessions) after a reset wipe.
# Sessions table is checked separately with the demo=1 filter.
_DEMO_SCOPED_SESSION_TABLES: tuple[str, ...] = (
    "appointments",
    "job_applications",
    "resume_versions",
    "daily_progress_snapshots",
    "engagement_events",
    "plan_history",
    "outcomes_records",
    "reminder_cooldowns",
    "worker_unavailability",
    "feedback_tokens",
    "visit_feedback",
    "resource_feedback",
    "record_profiles",
    "share_tokens",
)


# -------------------- Cycle 1: smoke wipe + reseed --------------------


def test_main_wipes_demo_sessions_and_reseeds(seeded_db_path: str) -> None:
    """End-to-end smoke: reset on a populated DB ends with the seed back in place."""
    summary = qc_reset.main(seeded_db_path)
    conn = sqlite3.connect(seeded_db_path)
    try:
        demo_count = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE demo = 1 AND id != '_advisor_audit'"
        ).fetchone()[0]
    finally:
        conn.close()
    # 5 sessions per city × 2 cities = 10 demo sessions after reseed.
    assert demo_count == 10
    assert summary["reseeded"] is True
    assert summary["sessions_after_reseed"] == 10


def test_main_wipe_only_when_no_reseed(seeded_db_path: str) -> None:
    """``reseed=False`` wipes demo rows and does NOT replant them."""
    summary = qc_reset.main(seeded_db_path, reseed=False)
    conn = sqlite3.connect(seeded_db_path)
    try:
        demo_count = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE demo = 1 AND id != '_advisor_audit'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert demo_count == 0
    assert summary["reseeded"] is False
    assert summary["sessions_after_reseed"] == 0


def test_main_returns_per_table_delete_counts(seeded_db_path: str) -> None:
    """Summary exposes per-table delete counts so ops can verify cascade."""
    summary = qc_reset.main(seeded_db_path, reseed=False)
    deleted = summary["deleted"]
    # The sessions row count should equal the seed's session count.
    assert deleted["sessions"] == 10
    # Every demo-scoped table key is present (some may be 0 if seed didn't plant rows).
    for table in _DEMO_SCOPED_SESSION_TABLES:
        assert table in deleted, f"{table} missing from delete summary"


# -------------------- Cycle 2: cascade coverage --------------------


def test_wipe_clears_every_demo_scoped_table(seeded_db_path: str) -> None:
    """After a wipe (no reseed) every demo-scoped table reports 0 demo rows."""
    qc_reset.main(seeded_db_path, reseed=False)
    conn = sqlite3.connect(seeded_db_path)
    try:
        for table in _DEMO_SCOPED_SESSION_TABLES:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table} "
                f"WHERE session_id IN (SELECT id FROM sessions WHERE demo = 1)"
            ).fetchone()[0]
            assert count == 0, f"{table} still has demo rows: {count}"
    finally:
        conn.close()


def test_wipe_clears_compliance_audit_for_demo_sessions(
    seeded_db_path: str,
) -> None:
    """``compliance_audit`` is keyed by sha256(session_id), wiped by hash."""
    import hashlib

    # Snapshot the demo session id hashes BEFORE the wipe (sessions row is
    # gone after) so we know exactly which audit rows must be missing.
    conn = sqlite3.connect(seeded_db_path)
    try:
        demo_ids = [
            row[0] for row in conn.execute(
                "SELECT id FROM sessions WHERE demo = 1 AND id != '_advisor_audit'"
            ).fetchall()
        ]
    finally:
        conn.close()
    demo_hashes = [hashlib.sha256(sid.encode()).hexdigest() for sid in demo_ids]

    qc_reset.main(seeded_db_path, reseed=False)

    conn = sqlite3.connect(seeded_db_path)
    try:
        placeholders = ",".join("?" * len(demo_hashes))
        count = conn.execute(
            f"SELECT COUNT(*) FROM compliance_audit "
            f"WHERE session_id_hash IN ({placeholders})",
            demo_hashes,
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 0


def test_wipe_clears_demo_advisor_tokens(seeded_db_path: str) -> None:
    """The two seeded ``advisor_tokens`` rows (one per city) are gone."""
    qc_reset.main(seeded_db_path, reseed=False)
    conn = sqlite3.connect(seeded_db_path)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM advisor_tokens "
            "WHERE advisor_id LIKE 'adv-demo-%'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 0


def test_wipe_clears_demo_sendgrid_events(seeded_db_path: str) -> None:
    """Sendgrid events with the deterministic ``demo-`` message_id prefix go away."""
    qc_reset.main(seeded_db_path, reseed=False)
    conn = sqlite3.connect(seeded_db_path)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM sendgrid_events "
            "WHERE message_id LIKE 'demo-%'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 0


# -------------------- Cycle 3: idempotency --------------------


def test_reset_is_idempotent_on_clean_db(reset_db_path: str) -> None:
    """Running reset on a never-seeded DB reseeds and produces 10 sessions."""
    summary_first = qc_reset.main(reset_db_path)
    summary_second = qc_reset.main(reset_db_path)
    assert summary_first["sessions_after_reseed"] == 10
    assert summary_second["sessions_after_reseed"] == 10


def test_reset_twice_produces_stable_state(seeded_db_path: str) -> None:
    """Two consecutive resets on a seeded DB end in the same state."""
    fixed_now = datetime(2026, 4, 24, 12, 0, 0, tzinfo=timezone.utc)
    qc_reset.main(seeded_db_path, now=fixed_now)
    snap1 = qc_seed_snapshot(seeded_db_path)
    qc_reset.main(seeded_db_path, now=fixed_now)
    snap2 = qc_seed_snapshot(seeded_db_path)
    assert snap1 == snap2


# -------------------- Cycle 4: non-demo data preserved --------------------


_SENTINEL_ID = "sentinel-non-demo-session"
_SENTINEL_TS = "2026-04-20T00:00:00+00:00"


def _plant_non_demo_sentinel(db_path: str) -> None:
    """Insert a non-demo session plus one child row in each scoped table."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, profile, "
            "expires_at, demo) VALUES (?, ?, '[]', '{}', ?, 0)",
            (_SENTINEL_ID, _SENTINEL_TS, "2099-12-31T00:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO appointments (session_id, type, title, starts_at, "
            "created_at) VALUES (?, 'career_center', 'sentinel', ?, ?)",
            (_SENTINEL_ID, _SENTINEL_TS, _SENTINEL_TS),
        )
        conn.execute(
            "INSERT INTO job_applications (session_id, status, created_at) "
            "VALUES (?, 'applied', ?)",
            (_SENTINEL_ID, _SENTINEL_TS),
        )
        conn.execute(
            "INSERT INTO engagement_events (session_id, category, "
            "payload_json, created_at) VALUES (?, 'sentinel', '{}', ?)",
            (_SENTINEL_ID, _SENTINEL_TS),
        )
        conn.execute(
            "INSERT INTO outcomes_records (session_id, event_type, "
            "payload_json, created_at) VALUES (?, 'sentinel', '{}', ?)",
            (_SENTINEL_ID, _SENTINEL_TS),
        )
        conn.commit()
    finally:
        conn.close()


def _count_sentinel_children(db_path: str) -> dict[str, int]:
    """Return per-table counts of rows linked to the sentinel session."""
    queries = {
        "appointments": "SELECT COUNT(*) FROM appointments WHERE session_id = ?",
        "job_applications": (
            "SELECT COUNT(*) FROM job_applications WHERE session_id = ?"
        ),
        "engagement_events": (
            "SELECT COUNT(*) FROM engagement_events WHERE session_id = ?"
        ),
        "outcomes_records": (
            "SELECT COUNT(*) FROM outcomes_records WHERE session_id = ?"
        ),
    }
    out: dict[str, int] = {}
    conn = sqlite3.connect(db_path)
    try:
        for key, sql in queries.items():
            out[key] = conn.execute(sql, (_SENTINEL_ID,)).fetchone()[0]
    finally:
        conn.close()
    return out


def test_non_demo_session_and_children_survive_reset(
    seeded_db_path: str,
) -> None:
    """A manually inserted non-demo session + child rows are NOT wiped."""
    _plant_non_demo_sentinel(seeded_db_path)
    qc_reset.main(seeded_db_path)
    conn = sqlite3.connect(seeded_db_path)
    try:
        session_row = conn.execute(
            "SELECT demo FROM sessions WHERE id = ?", (_SENTINEL_ID,),
        ).fetchone()
    finally:
        conn.close()
    counts = _count_sentinel_children(seeded_db_path)
    assert session_row is not None, "sentinel session was deleted"
    assert session_row[0] == 0, "sentinel demo flag mutated"
    assert counts["appointments"] == 1
    assert counts["job_applications"] == 1
    assert counts["engagement_events"] == 1
    assert counts["outcomes_records"] == 1


def test_non_demo_advisor_token_survives_reset(seeded_db_path: str) -> None:
    """A non-demo ``advisor_tokens`` row is preserved by the reset."""
    conn = sqlite3.connect(seeded_db_path)
    try:
        conn.execute(
            "INSERT INTO advisor_tokens (token_hash, advisor_id, city, "
            "issued_at) VALUES ('nondemo-hash', 'real-advisor', "
            "'montgomery', '2026-04-01T00:00:00+00:00')"
        )
        conn.commit()
    finally:
        conn.close()

    qc_reset.main(seeded_db_path)

    conn = sqlite3.connect(seeded_db_path)
    try:
        row = conn.execute(
            "SELECT advisor_id FROM advisor_tokens WHERE token_hash = ?",
            ("nondemo-hash",),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[0] == "real-advisor"


def test_advisor_audit_placeholder_session_is_preserved(
    seeded_db_path: str,
) -> None:
    """The ``_advisor_audit`` placeholder session row is preserved.

    Although it carries ``demo=1``, audit-write code creates it on
    demand and other code paths assume its presence. The reset wipes
    its child engagement events but keeps the placeholder row itself.
    """
    placeholder_id = "_advisor_audit"
    now_iso = "2026-04-20T00:00:00+00:00"
    conn = sqlite3.connect(seeded_db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id, created_at, barriers, "
            "profile, expires_at, demo) VALUES (?, ?, '[]', '{}', ?, 1)",
            (placeholder_id, now_iso, "2099-12-31T00:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO engagement_events (session_id, category, "
            "payload_json, created_at) "
            "VALUES (?, 'advisor_action', '{\"demo\": true}', ?)",
            (placeholder_id, now_iso),
        )
        conn.commit()
    finally:
        conn.close()

    qc_reset.main(seeded_db_path)

    conn = sqlite3.connect(seeded_db_path)
    try:
        sess = conn.execute(
            "SELECT id FROM sessions WHERE id = ?", (placeholder_id,),
        ).fetchone()
        ev_count = conn.execute(
            "SELECT COUNT(*) FROM engagement_events WHERE session_id = ?",
            (placeholder_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert sess is not None, "placeholder session was deleted"
    assert ev_count == 0, "placeholder engagement_events should be wiped"


# -------------------- Cycle 5: determinism --------------------


def test_reset_reseed_matches_first_seed_snapshot(reset_db_path: str) -> None:
    """seed → snapshot → reset+reseed → snapshot — the two snapshots match."""
    fixed_now = datetime(2026, 4, 24, 12, 0, 0, tzinfo=timezone.utc)
    seed_worker_companion_sessions(db_path=reset_db_path, now=fixed_now)
    snap_before = qc_seed_snapshot(reset_db_path)
    qc_reset.main(reset_db_path, now=fixed_now)
    snap_after = qc_seed_snapshot(reset_db_path)
    assert snap_before == snap_after


# -------------------- Cycle 6: speed budget --------------------


def test_reset_runs_under_five_seconds(seeded_db_path: str) -> None:
    """Reset on a populated demo DB completes within the 5-second budget."""
    start = time.perf_counter()
    qc_reset.main(seeded_db_path)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"reset took {elapsed:.3f}s (>5s budget)"


# -------------------- Cycle 7: CLI argparse layer --------------------


def test_cli_runs_with_db_path_argument(reset_db_path: str) -> None:
    """``python scripts/qc_reset.py --db-path …`` exits 0 and prints a summary."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "qc_reset.py"),
         "--db-path", reset_db_path],
        capture_output=True, text=True, cwd=str(REPO_ROOT / "backend"),
    )
    assert proc.returncode == 0, (
        f"qc_reset.py exited {proc.returncode}\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    # Summary line names the reseed result so ops can scan it visually.
    assert "reseeded" in proc.stdout.lower() or "sessions" in proc.stdout.lower()


def test_cli_no_reseed_flag_skips_reseed(seeded_db_path: str) -> None:
    """``--no-reseed`` wipes only and reports zero sessions after reseed."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "qc_reset.py"),
         "--db-path", seeded_db_path, "--no-reseed"],
        capture_output=True, text=True, cwd=str(REPO_ROOT / "backend"),
    )
    assert proc.returncode == 0, (
        f"qc_reset.py exited {proc.returncode}\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    conn = sqlite3.connect(seeded_db_path)
    try:
        demo_count = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE demo = 1 AND id != '_advisor_audit'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert demo_count == 0
