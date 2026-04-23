"""Tests for m002_s12_worker_companion migration (T12.1).

Covers the full 13-table S12 worker-companion schema:
- All 13 tables present after upgrade
- All session_id columns TEXT
- All session FKs declare ON DELETE CASCADE
- Required indexes present
- plan_history schema + cap comment
- Idempotent upgrade
- Downgrade round-trip preserves m001 tables
- schema_migrations records version 2
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.migrations import m001_initial, runner


# -------------------- Shared constants --------------------


EXPECTED_TABLES = {
    "appointments",
    "job_applications",
    "resume_versions",
    "daily_progress_snapshots",
    "engagement_events",
    "plan_history",
    "outcomes_records",
    "reminder_cooldowns",
    "nightly_run_log",
    "scheduler_leases",
    "worker_unavailability",
    "feature_flag_audit",
    "sendgrid_events",
}

SESSION_FK_TABLES = {
    "appointments",
    "job_applications",
    "resume_versions",
    "daily_progress_snapshots",
    "engagement_events",
    "plan_history",
    "outcomes_records",
    "reminder_cooldowns",
    "worker_unavailability",
}

EXPECTED_INDEXES = {
    "idx_appointments_session_id",
    "idx_appointments_starts_at",
    "idx_appointments_status",
    "idx_job_applications_session_id",
    "idx_job_applications_status",
    "idx_job_applications_applied_date",
    "idx_resume_versions_session_id",
    "idx_daily_progress_snapshots_session_id",
    "idx_daily_progress_snapshots_date",
    "idx_engagement_events_session_id",
    "idx_engagement_events_category",
    "idx_engagement_events_created_at",
    "idx_plan_history_session_id",
    "idx_plan_history_archived_at",
    "idx_outcomes_records_session_id",
    "idx_outcomes_records_event_type",
    "idx_outcomes_records_created_at",
    "idx_reminder_cooldowns_session_category",
    "idx_nightly_run_log_start_ts",
    "idx_nightly_run_log_city",
    "idx_worker_unavailability_session_id",
    "idx_feature_flag_audit_flag_name_timestamp",
    "idx_sendgrid_events_event_type",
    "idx_sendgrid_events_email",
    "idx_sendgrid_events_created_at",
}


# -------------------- Helpers --------------------


def _fresh_db(tmp_path, name: str = "m002.db") -> str:
    """Create a DB with only m001 applied — baseline for m002 tests."""
    db_path = str(tmp_path / name)
    conn = sqlite3.connect(db_path)
    try:
        m001_initial.upgrade(conn)
        conn.commit()
    finally:
        conn.close()
    return db_path


def _apply_m002(db_path: str) -> None:
    from app.core.migrations import m002_s12_worker_companion

    conn = sqlite3.connect(db_path)
    try:
        m002_s12_worker_companion.upgrade(conn)
        conn.commit()
    finally:
        conn.close()


def _all_tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row[0] for row in rows}


def _all_indexes(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row[0] for row in rows}


# -------------------- Table + column presence --------------------


def test_upgrade_creates_all_13_tables(tmp_path):
    """m002.upgrade creates all 13 expected tables."""
    db_path = _fresh_db(tmp_path)
    _apply_m002(db_path)

    conn = sqlite3.connect(db_path)
    try:
        tables = _all_tables(conn)
        assert EXPECTED_TABLES.issubset(tables), (
            f"Missing tables: {EXPECTED_TABLES - tables}"
        )
    finally:
        conn.close()


def test_all_session_id_columns_are_TEXT(tmp_path):
    """Every table with a session_id column declares it TEXT."""
    db_path = _fresh_db(tmp_path)
    _apply_m002(db_path)

    conn = sqlite3.connect(db_path)
    try:
        for table in SESSION_FK_TABLES:
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            col_map = {row[1]: row for row in cols}
            assert "session_id" in col_map, f"{table} missing session_id"
            assert col_map["session_id"][2].upper() == "TEXT", (
                f"{table}.session_id type is {col_map['session_id'][2]}, expected TEXT"
            )
    finally:
        conn.close()


def test_all_session_fks_cascade_on_delete(tmp_path):
    """Every table with a session_id FK declares ON DELETE CASCADE."""
    db_path = _fresh_db(tmp_path)
    _apply_m002(db_path)

    conn = sqlite3.connect(db_path)
    try:
        for table in SESSION_FK_TABLES:
            fks = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
            # Each row: (id, seq, table, from, to, on_update, on_delete, match)
            session_fks = [fk for fk in fks if fk[3] == "session_id"]
            assert session_fks, f"{table} has no FK on session_id"
            for fk in session_fks:
                assert fk[2] == "sessions", (
                    f"{table}.session_id references {fk[2]}, expected sessions"
                )
                assert fk[6] == "CASCADE", (
                    f"{table}.session_id on_delete is {fk[6]}, expected CASCADE"
                )
    finally:
        conn.close()


# -------------------- Indexes --------------------


def test_required_indexes_present(tmp_path):
    """All indexes listed in the task spec are created."""
    db_path = _fresh_db(tmp_path)
    _apply_m002(db_path)

    conn = sqlite3.connect(db_path)
    try:
        indexes = _all_indexes(conn)
        missing = EXPECTED_INDEXES - indexes
        assert not missing, f"Missing indexes: {missing}"
    finally:
        conn.close()


# -------------------- plan_history schema + cap comment --------------------


def test_plan_history_schema(tmp_path):
    """plan_history has the exact expected columns."""
    db_path = _fresh_db(tmp_path)
    _apply_m002(db_path)

    conn = sqlite3.connect(db_path)
    try:
        cols = conn.execute("PRAGMA table_info(plan_history)").fetchall()
        names = {row[1] for row in cols}
        expected = {
            "id",
            "session_id",
            "archived_at",
            "plan_json",
            "refresh_reason",
            "triggering_event",
        }
        assert expected.issubset(names), (
            f"plan_history missing columns: {expected - names}"
        )
    finally:
        conn.close()


def test_plan_history_cap_comment_present():
    """m002 source contains the cap-of-20 comment referencing T12.24."""
    module_path = (
        Path(__file__).parent.parent
        / "app"
        / "core"
        / "migrations"
        / "m002_s12_worker_companion.py"
    )
    src = module_path.read_text()
    assert "cap of 20 per session enforced in T12.24" in src, (
        "plan_history cap comment missing"
    )


# -------------------- Idempotency --------------------


def test_idempotent(tmp_path):
    """Applying m002 twice on a fresh DB produces the same table set with no errors."""
    db_path = _fresh_db(tmp_path)
    _apply_m002(db_path)

    conn = sqlite3.connect(db_path)
    try:
        tables_first = _all_tables(conn)
    finally:
        conn.close()

    # Second application — should not error
    _apply_m002(db_path)

    conn = sqlite3.connect(db_path)
    try:
        tables_second = _all_tables(conn)
    finally:
        conn.close()

    assert tables_first == tables_second


# -------------------- Downgrade round-trip --------------------


def _seed_session(db_path: str, session_id: str) -> None:
    """Insert a session row so FK inserts into m002 tables succeed."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, "2026-04-23T00:00:00Z", "[]", "2026-05-23T00:00:00Z"),
        )
        conn.commit()
    finally:
        conn.close()


def _run_m002_downgrade(db_path: str) -> None:
    from app.core.migrations import m002_s12_worker_companion

    conn = sqlite3.connect(db_path)
    try:
        m002_s12_worker_companion.downgrade(conn)
        conn.commit()
    finally:
        conn.close()


def _seed_via_connection(db_path: str, session_id: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        _seed_all_m002_tables(conn, session_id)
        conn.commit()
    finally:
        conn.close()


def test_downgrade_round_trip(tmp_path):
    """Seed a session, apply m002, insert rows in each new table, downgrade — m001 intact."""
    db_path = _fresh_db(tmp_path)
    _seed_session(db_path, "sess-round-trip")
    _apply_m002(db_path)
    _seed_via_connection(db_path, "sess-round-trip")
    _run_m002_downgrade(db_path)

    # All 13 new tables gone, sessions intact
    conn = sqlite3.connect(db_path)
    try:
        tables = _all_tables(conn)
        leftover = EXPECTED_TABLES & tables
        assert not leftover, f"Downgrade left tables: {leftover}"
        assert "sessions" in tables, "Downgrade clobbered m001 sessions table"
        row = conn.execute(
            "SELECT id FROM sessions WHERE id = 'sess-round-trip'"
        ).fetchone()
        assert row is not None, "Session data should survive m002 downgrade"
    finally:
        conn.close()


_NOW = "2026-04-23T00:00:00Z"

# (sql, params_factory) pairs — params_factory(session_id) returns the tuple.
_SEED_ROWS: tuple[tuple[str, str], ...] = (
    (
        "INSERT INTO appointments (id, session_id, type, title, starts_at, ends_at, "
        "location_name, location_address, barrier_link, status, source, notes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        "appointments",
    ),
    (
        "INSERT INTO job_applications (id, session_id, match_source, match_url, company, "
        "role, resume_version_id, status, applied_date, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        "job_applications",
    ),
    (
        "INSERT INTO resume_versions (id, session_id, doc_type, version_counter, markdown, "
        "target_job_source, target_job_url, barriers_framed_json, generation_method, use_counter, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        "resume_versions",
    ),
    (
        "INSERT INTO daily_progress_snapshots (id, session_id, date, expected_actions_json, "
        "evidence_json, classifications_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        "daily_progress_snapshots",
    ),
    (
        "INSERT INTO engagement_events (id, session_id, category, payload_json, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        "engagement_events",
    ),
    (
        "INSERT INTO plan_history (id, session_id, archived_at, plan_json, refresh_reason, triggering_event) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        "plan_history",
    ),
    (
        "INSERT INTO outcomes_records (id, session_id, event_type, payload_json, created_at, "
        "barriers_cleared_snapshot_json) VALUES (?, ?, ?, ?, ?, ?)",
        "outcomes_records",
    ),
    (
        "INSERT INTO reminder_cooldowns (id, session_id, category, last_sent_at, stall_level) "
        "VALUES (?, ?, ?, ?, ?)",
        "reminder_cooldowns",
    ),
    (
        "INSERT INTO nightly_run_log (id, city, sessions_processed, emails_sent, errors, "
        "duration_sec, start_ts, end_ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        "nightly_run_log",
    ),
    (
        "INSERT INTO scheduler_leases (lease_name, holder, acquired_at, expires_at) "
        "VALUES (?, ?, ?, ?)",
        "scheduler_leases",
    ),
    (
        "INSERT INTO worker_unavailability (id, session_id, day_of_week, start_time, end_time, reason) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        "worker_unavailability",
    ),
    (
        "INSERT INTO feature_flag_audit (id, flag_name, old_value, new_value, reason, "
        "actor_token_hash, source_ip, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        "feature_flag_audit",
    ),
    (
        "INSERT INTO sendgrid_events (id, event_type, email, message_id, reason, "
        "raw_payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        "sendgrid_events",
    ),
)


def _seed_params(table: str, session_id: str) -> tuple:
    """Build a single-row insert tuple for each table."""
    n = _NOW
    return {
        "appointments": (1, session_id, "interview", "Title", n, n, "Loc", "Addr", None, "scheduled", "manual", None, n),
        "job_applications": (1, session_id, "indeed", "http://example.com", "Co", "Role", None, "applied", n, n),
        "resume_versions": (1, session_id, "resume", 1, "# resume", "indeed", "http://x", "[]", "template", 0, n),
        "daily_progress_snapshots": (1, session_id, "2026-04-23", "[]", "[]", "[]", n),
        "engagement_events": (1, session_id, "email_sent", "{}", n),
        "plan_history": (1, session_id, n, "{}", "manual_refresh", "user_action"),
        "outcomes_records": (1, session_id, "application_submitted", "{}", n, "[]"),
        "reminder_cooldowns": (1, session_id, "daily_nudge", n, 1),
        "nightly_run_log": (1, "montgomery", 0, 0, 0, 0.0, n, n),
        "scheduler_leases": ("nightly", "worker-1", n, n),
        "worker_unavailability": (1, session_id, 1, "09:00", "17:00", "class"),
        "feature_flag_audit": (1, "FEATURE_X", "false", "true", "test", "hash", "127.0.0.1", n),
        "sendgrid_events": (1, "delivered", "a@b.c", "mid-1", None, "{}", n),
    }[table]


def _seed_all_m002_tables(conn: sqlite3.Connection, session_id: str) -> None:
    """Insert a single row into every table created by m002."""
    for sql, table in _SEED_ROWS:
        conn.execute(sql, _seed_params(table, session_id))


# -------------------- Runner integration --------------------


def test_schema_migrations_version_2_recorded(tmp_path):
    """After runner.apply_pending, schema_migrations contains version 2."""
    db_path = str(tmp_path / "run.db")
    applied = runner.apply_pending(db_path)
    assert "m002_s12_worker_companion" in applied

    conn = sqlite3.connect(db_path)
    try:
        versions = {
            row[0]
            for row in conn.execute(
                "SELECT version FROM schema_migrations"
            ).fetchall()
        }
        assert 2 in versions
    finally:
        conn.close()


# -------------------- Module-shape sanity --------------------


def test_m002_exports_schema_version_and_funcs():
    """m002 module exports SCHEMA_VERSION=2, upgrade, downgrade."""
    from app.core.migrations import m002_s12_worker_companion as m002

    assert hasattr(m002, "SCHEMA_VERSION")
    assert m002.SCHEMA_VERSION == 2
    assert callable(getattr(m002, "upgrade", None))
    assert callable(getattr(m002, "downgrade", None))
