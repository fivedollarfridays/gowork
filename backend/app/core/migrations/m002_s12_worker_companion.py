"""Migration 002 — S12 worker-companion schema (13 tables).

Adds all tables required across S12a + S12b:
- appointments, job_applications, resume_versions, daily_progress_snapshots
- engagement_events, plan_history, outcomes_records, reminder_cooldowns
- nightly_run_log, scheduler_leases, worker_unavailability
- feature_flag_audit, sendgrid_events

All session_id FKs declare ON DELETE CASCADE (TEXT, matching sessions.id).
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 2


# -------------------- Table DDL --------------------
#
# Each entry is a single CREATE TABLE IF NOT EXISTS statement. Statements are
# applied verbatim via executescript so the migration is idempotent on re-run.

_TABLE_DDL: tuple[str, ...] = (
    # appointments — S12a worker appointment records
    """
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        starts_at TEXT NOT NULL,
        ends_at TEXT,
        location_name TEXT,
        location_address TEXT,
        barrier_link TEXT,
        status TEXT NOT NULL DEFAULT 'scheduled',
        source TEXT,
        notes TEXT,
        created_at TEXT NOT NULL
    )
    """,
    # job_applications — S12a job application lifecycle
    """
    CREATE TABLE IF NOT EXISTS job_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        match_source TEXT,
        match_url TEXT,
        company TEXT,
        role TEXT,
        resume_version_id INTEGER,
        status TEXT NOT NULL DEFAULT 'applied',
        applied_date TEXT,
        created_at TEXT NOT NULL
    )
    """,
    # resume_versions — S12b resume + cover letter versions
    """
    CREATE TABLE IF NOT EXISTS resume_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        doc_type TEXT NOT NULL,
        version_counter INTEGER NOT NULL,
        markdown TEXT NOT NULL,
        target_job_source TEXT,
        target_job_url TEXT,
        barriers_framed_json TEXT,
        generation_method TEXT,
        use_counter INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """,
    # daily_progress_snapshots — per-day retro results
    """
    CREATE TABLE IF NOT EXISTS daily_progress_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        date TEXT NOT NULL,
        expected_actions_json TEXT,
        evidence_json TEXT,
        classifications_json TEXT,
        created_at TEXT NOT NULL
    )
    """,
    # engagement_events — email sends, bounces, stalls, auto-advances
    """
    CREATE TABLE IF NOT EXISTS engagement_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        category TEXT NOT NULL,
        payload_json TEXT,
        created_at TEXT NOT NULL
    )
    """,
    # plan_history — S12b archived plans from refresh
    # cap of 20 per session enforced in T12.24 (application code; NOT at schema level)
    """
    CREATE TABLE IF NOT EXISTS plan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        archived_at TEXT NOT NULL,
        plan_json TEXT NOT NULL,
        refresh_reason TEXT,
        triggering_event TEXT
    )
    """,
    # outcomes_records — append-only outcomes signal store (T12.0a consumer)
    """
    CREATE TABLE IF NOT EXISTS outcomes_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        event_type TEXT NOT NULL,
        payload_json TEXT,
        created_at TEXT NOT NULL,
        barriers_cleared_snapshot_json TEXT
    )
    """,
    # reminder_cooldowns — S12b dedup for reminder engine
    """
    CREATE TABLE IF NOT EXISTS reminder_cooldowns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        category TEXT NOT NULL,
        last_sent_at TEXT NOT NULL,
        stall_level INTEGER NOT NULL DEFAULT 0
    )
    """,
    # nightly_run_log — structured accounting per nightly run
    """
    CREATE TABLE IF NOT EXISTS nightly_run_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        sessions_processed INTEGER NOT NULL DEFAULT 0,
        emails_sent INTEGER NOT NULL DEFAULT 0,
        errors INTEGER NOT NULL DEFAULT 0,
        duration_sec REAL,
        start_ts TEXT NOT NULL,
        end_ts TEXT
    )
    """,
    # scheduler_leases — multi-worker scheduler lock (table present for S13 switch)
    """
    CREATE TABLE IF NOT EXISTS scheduler_leases (
        lease_name TEXT PRIMARY KEY,
        holder TEXT NOT NULL,
        acquired_at TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )
    """,
    # worker_unavailability — S12b worker-declared availability blocks
    """
    CREATE TABLE IF NOT EXISTS worker_unavailability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        day_of_week INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        reason TEXT
    )
    """,
    # feature_flag_audit — T12.0b audit trail
    """
    CREATE TABLE IF NOT EXISTS feature_flag_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flag_name TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        reason TEXT,
        actor_token_hash TEXT,
        source_ip TEXT,
        timestamp TEXT NOT NULL
    )
    """,
    # sendgrid_events — SendGrid Event Webhook ingestion
    """
    CREATE TABLE IF NOT EXISTS sendgrid_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        email TEXT,
        message_id TEXT,
        reason TEXT,
        raw_payload_json TEXT,
        created_at TEXT NOT NULL
    )
    """,
)


# -------------------- Index DDL --------------------

_INDEX_DDL: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_appointments_session_id ON appointments(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_appointments_starts_at ON appointments(starts_at)",
    "CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)",
    "CREATE INDEX IF NOT EXISTS idx_job_applications_session_id ON job_applications(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(status)",
    "CREATE INDEX IF NOT EXISTS idx_job_applications_applied_date ON job_applications(applied_date)",
    "CREATE INDEX IF NOT EXISTS idx_resume_versions_session_id ON resume_versions(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_daily_progress_snapshots_session_id ON daily_progress_snapshots(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_daily_progress_snapshots_date ON daily_progress_snapshots(date)",
    "CREATE INDEX IF NOT EXISTS idx_engagement_events_session_id ON engagement_events(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_engagement_events_category ON engagement_events(category)",
    "CREATE INDEX IF NOT EXISTS idx_engagement_events_created_at ON engagement_events(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_plan_history_session_id ON plan_history(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_plan_history_archived_at ON plan_history(archived_at)",
    "CREATE INDEX IF NOT EXISTS idx_outcomes_records_session_id ON outcomes_records(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_outcomes_records_event_type ON outcomes_records(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_outcomes_records_created_at ON outcomes_records(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_reminder_cooldowns_session_category ON reminder_cooldowns(session_id, category)",
    "CREATE INDEX IF NOT EXISTS idx_nightly_run_log_start_ts ON nightly_run_log(start_ts)",
    "CREATE INDEX IF NOT EXISTS idx_nightly_run_log_city ON nightly_run_log(city)",
    "CREATE INDEX IF NOT EXISTS idx_worker_unavailability_session_id ON worker_unavailability(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_feature_flag_audit_flag_name_timestamp ON feature_flag_audit(flag_name, timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_sendgrid_events_event_type ON sendgrid_events(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_sendgrid_events_email ON sendgrid_events(email)",
    "CREATE INDEX IF NOT EXISTS idx_sendgrid_events_created_at ON sendgrid_events(created_at)",
)


# -------------------- Downgrade order --------------------
#
# Child tables first (none of these reference each other, but order by the
# pattern established in m001 for readability / future cross-refs).

_DOWNGRADE_ORDER: tuple[str, ...] = (
    "sendgrid_events",
    "feature_flag_audit",
    "worker_unavailability",
    "scheduler_leases",
    "nightly_run_log",
    "reminder_cooldowns",
    "outcomes_records",
    "plan_history",
    "engagement_events",
    "daily_progress_snapshots",
    "resume_versions",
    "job_applications",
    "appointments",
)


def upgrade(conn: sqlite3.Connection) -> None:
    """Apply migration 002 — create all S12 worker-companion tables + indexes."""
    for ddl in _TABLE_DDL:
        conn.execute(ddl)
    for ddl in _INDEX_DDL:
        conn.execute(ddl)


def downgrade(conn: sqlite3.Connection) -> None:
    """Drop all tables created by migration 002 (indexes drop with their tables)."""
    for table in _DOWNGRADE_ORDER:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
