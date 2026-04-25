"""Compliance cascade verification (T13.70).

Goal
----
Lock in the invariant that ``compliance.delete.full_delete`` clears
**every** session-scoped row from the database. New session-scoped
tables added in future migrations must either:

1. declare an ``ON DELETE CASCADE`` FK to ``sessions(id)`` (so they
   ride the SQLite cascade for free), **or**
2. be added to the explicit cascade list inside ``delete.py`` (the
   ``_NON_CASCADING_TABLES`` tuple), **or**
3. be added to the allowlist below with a documented reason.

Otherwise this test fails with the offending table name — the
"new session-scoped table without cascade -> CI red" guarantee.

Introspection strategy
----------------------
Two queries against an apply-all-migrations DB:

* ``SELECT name FROM sqlite_master WHERE type='table'`` — the canonical
  user-table list (sqlite_* internal tables filtered out).
* For each table, ``PRAGMA foreign_key_list(<table>)`` reports every
  declared FK; we keep only those pointing at ``sessions(id)``.
* For each table, ``PRAGMA table_info(<table>)`` reports columns; we
  also flag any table carrying a literal ``session_id`` column even
  when no FK was declared (m001 ``record_profiles`` /
  ``feedback_tokens`` / ``visit_feedback`` / ``resource_feedback`` /
  ``share_tokens`` predate the S12 cascade contract).

The union of FK-bearing and session_id-column-bearing tables is the
"session-scoped" inventory the cascade must cover.

Allowlist (rows intentionally retained)
---------------------------------------
* ``compliance_audit`` — written by ``full_delete`` itself, with a
  hashed session id; this row IS the audit trail and must outlive
  the deletion. The column is named ``session_id_hash`` (not
  ``session_id``) so it never appears in the introspection lists,
  but the allowlist documents the intent for completeness.

Cascade gap fixed by this task
------------------------------
Introspection plus a seed-every-table fixture revealed that the m001
session-keyed tables without FKs were not being cleared by
``full_delete`` — only ``record_profiles`` had been added to the
non-cascade list. Added to ``_NON_CASCADING_TABLES``:

* ``feedback_tokens``    — m001 worker feedback tokens
* ``visit_feedback``     — m001 visit feedback responses
* ``resource_feedback``  — m001 per-resource feedback
* ``share_tokens``       — m001 plan share tokens

The S12 m002 children (appointments, resume_versions, etc.) all carry
``ON DELETE CASCADE`` FKs and were already covered by the implicit
cascade chain triggered when the ``sessions`` row is deleted.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner

# --------------------------------------------------------------- constants

# Tables intentionally retained after ``full_delete`` — each entry must
# carry a one-line reason. Inclusion is checked by the schema-drift
# guard test below.
_RETAIN_ALLOWLIST: dict[str, str] = {
    # The audit table stores ``session_id_hash`` (sha256), never the raw
    # id. ``full_delete`` writes one row HERE before cascading, and that
    # row is the immutable record of the deletion. Retained by design.
    "compliance_audit": (
        "audit trail — stores hashed session id, written by full_delete"
    ),
}


# Sentinel for the seeded test session — kept short so it fits inside
# every short ``session_id`` text column without truncation surprises.
_SESSION_ID = "sess-cascade-test"

# Frozen reference instant for any seeded timestamps. Determinism: every
# row inserted by this module uses this clock so the test never races
# against wall-clock millisecond boundaries.
_NOW = datetime(2026, 4, 24, 12, 0, 0, tzinfo=timezone.utc)
_NOW_ISO = _NOW.isoformat()


# --------------------------------------------------------------- introspection

def _user_tables(conn: sqlite3.Connection) -> list[str]:
    """All user-defined tables (sqlite_* / schema_migrations excluded)."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' "
        "  AND name NOT LIKE 'sqlite_%' "
        "  AND name != 'schema_migrations' "
        "ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def _tables_with_fk_to_sessions(conn: sqlite3.Connection) -> list[str]:
    """Tables whose ``foreign_key_list`` references ``sessions(id)``."""
    found: list[str] = []
    for table in _user_tables(conn):
        for fk in conn.execute(f"PRAGMA foreign_key_list({table})").fetchall():
            # PRAGMA columns: id, seq, table, from, to, on_update, on_delete, match
            if fk[2] == "sessions" and fk[4] == "id":
                found.append(table)
                break
    return sorted(found)


def _tables_with_session_id_column(conn: sqlite3.Connection) -> list[str]:
    """Tables that carry a literal ``session_id`` column (FK or not)."""
    found: list[str] = []
    for table in _user_tables(conn):
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if "session_id" in cols:
            found.append(table)
    return sorted(found)


def _session_scoped_tables(conn: sqlite3.Connection) -> list[str]:
    """Union of FK-bearing + session_id-column-bearing tables."""
    union = set(_tables_with_fk_to_sessions(conn))
    union.update(_tables_with_session_id_column(conn))
    return sorted(union)


# --------------------------------------------------------------- seeding

def _seed_session_row(conn: sqlite3.Connection, sid: str) -> None:
    """Insert the parent ``sessions`` row the cascade hangs off of."""
    expires = (_NOW + timedelta(days=30)).isoformat()
    conn.execute(
        "INSERT INTO sessions (id, created_at, barriers, expires_at) "
        "VALUES (?, ?, ?, ?)",
        (sid, _NOW_ISO, "[]", expires),
    )


# Per-table seed SQL. Using a dispatch dict (not introspection-driven
# INSERTs) because each table has its own NOT NULL columns; a generic
# "insert with session_id only" would fail on m001 NOT NULL constraints.
# When a NEW session-scoped table lands without an entry here, the
# pre-assert in :func:`test_full_delete_clears_every_session_scoped_table`
# fails loudly (count == 0 before the action), which surfaces as a
# missing-seeder error, prompting the dev to add a seed entry plus
# decide cascade vs allowlist.
def _seed_appointments(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO appointments (session_id, type, title, starts_at, "
        "status, created_at) VALUES (?, 'dmv', 'DMV', ?, 'scheduled', ?)",
        (sid, _NOW_ISO, _NOW_ISO),
    )


def _seed_job_applications(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO job_applications (session_id, company, role, status, "
        "created_at) VALUES (?, 'Acme', 'welder', 'applied', ?)",
        (sid, _NOW_ISO),
    )


def _seed_resume_versions(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO resume_versions (session_id, doc_type, version_counter, "
        "markdown, use_counter, created_at) "
        "VALUES (?, 'resume', 1, '# resume', 0, ?)",
        (sid, _NOW_ISO),
    )


def _seed_daily_progress_snapshots(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO daily_progress_snapshots (session_id, date, created_at) "
        "VALUES (?, '2026-04-22', ?)",
        (sid, _NOW_ISO),
    )


def _seed_engagement_events(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO engagement_events (session_id, category, payload_json, "
        "created_at) VALUES (?, 'email_sent', '{}', ?)",
        (sid, _NOW_ISO),
    )


def _seed_plan_history(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO plan_history (session_id, archived_at, plan_json) "
        "VALUES (?, ?, '{}')",
        (sid, _NOW_ISO),
    )


def _seed_outcomes_records(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO outcomes_records (session_id, event_type, payload_json, "
        "created_at) VALUES (?, 'app', '{}', ?)",
        (sid, _NOW_ISO),
    )


def _seed_reminder_cooldowns(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO reminder_cooldowns (session_id, category, last_sent_at, "
        "stall_level) VALUES (?, 'digest', ?, 1)",
        (sid, _NOW_ISO),
    )


def _seed_worker_unavailability(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO worker_unavailability (session_id, day_of_week, "
        "start_time, end_time) VALUES (?, 1, '09:00', '17:00')",
        (sid,),
    )


def _seed_record_profiles(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO record_profiles (session_id, record_types, "
        "charge_categories) VALUES (?, '[]', '[]')",
        (sid,),
    )


def _seed_feedback_tokens(conn: sqlite3.Connection, sid: str) -> None:
    expires = (_NOW + timedelta(hours=24)).isoformat()
    conn.execute(
        "INSERT INTO feedback_tokens (token, session_id, created_at, "
        "expires_at) VALUES (?, ?, ?, ?)",
        (f"tok-{sid}", sid, _NOW_ISO, expires),
    )


def _seed_visit_feedback(conn: sqlite3.Connection, sid: str) -> None:
    conn.execute(
        "INSERT INTO visit_feedback (session_id, submitted_at, "
        "made_it_to_center, plan_accuracy) VALUES (?, ?, 1, 5)",
        (sid, _NOW_ISO),
    )


def _seed_resource_feedback(conn: sqlite3.Connection, sid: str) -> None:
    # resource_feedback has UNIQUE(resource_id, session_id) and a FK to
    # resources(id). Plant a dummy resource so the FK is happy.
    conn.execute(
        "INSERT INTO resources (id, name, category) VALUES (1, 'X', 'food')"
    )
    conn.execute(
        "INSERT INTO resource_feedback (resource_id, session_id, helpful, "
        "submitted_at) VALUES (1, ?, 1, ?)",
        (sid, _NOW_ISO),
    )


def _seed_share_tokens(conn: sqlite3.Connection, sid: str) -> None:
    expires = (_NOW + timedelta(days=7)).isoformat()
    conn.execute(
        "INSERT INTO share_tokens (token, session_id, created_at, "
        "expires_at) VALUES (?, ?, ?, ?)",
        (f"share-{sid}", sid, _NOW_ISO, expires),
    )


_SEEDERS: dict[str, callable] = {
    "appointments": _seed_appointments,
    "job_applications": _seed_job_applications,
    "resume_versions": _seed_resume_versions,
    "daily_progress_snapshots": _seed_daily_progress_snapshots,
    "engagement_events": _seed_engagement_events,
    "plan_history": _seed_plan_history,
    "outcomes_records": _seed_outcomes_records,
    "reminder_cooldowns": _seed_reminder_cooldowns,
    "worker_unavailability": _seed_worker_unavailability,
    "record_profiles": _seed_record_profiles,
    "feedback_tokens": _seed_feedback_tokens,
    "visit_feedback": _seed_visit_feedback,
    "resource_feedback": _seed_resource_feedback,
    "share_tokens": _seed_share_tokens,
}


def _seed_full_session(conn: sqlite3.Connection, sid: str) -> None:
    """Insert the session row plus one row per session-scoped table."""
    _seed_session_row(conn, sid)
    for table in _session_scoped_tables(conn):
        seeder = _SEEDERS.get(table)
        if seeder is None:
            # Fail fast inside the seeder so the test author sees exactly
            # which table needs a seed entry.
            raise AssertionError(
                f"No seed helper for session-scoped table {table!r}. "
                f"Add a _seed_{table} entry in _SEEDERS, then decide "
                "whether full_delete needs to cover it (cascade list) "
                "or whether it belongs in _RETAIN_ALLOWLIST."
            )
        seeder(conn, sid)


def _count_for_session(conn: sqlite3.Connection, table: str, sid: str) -> int:
    return conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE session_id = ?", (sid,),
    ).fetchone()[0]


# --------------------------------------------------------------- fixtures

@pytest.fixture
def cascade_db(tmp_path: Path) -> str:
    """Migrated DB seeded with one row in every session-scoped table."""
    db_path = str(tmp_path / "cascade.db")
    runner.apply_pending(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        _seed_full_session(conn, _SESSION_ID)
        conn.commit()
    finally:
        conn.close()
    return db_path


# --------------------------------------------------------------- introspection sanity

def test_introspection_returns_expected_session_scoped_tables(
    cascade_db: str,
) -> None:
    """Schema introspection must surface the canonical inventory.

    Acts as a sanity check on the introspection helpers themselves —
    if PRAGMA semantics ever change, this fails before the cascade
    test gets a chance to be misleading.
    """
    conn = sqlite3.connect(cascade_db)
    try:
        scoped = set(_session_scoped_tables(conn))
    finally:
        conn.close()

    # FK-bearing tables (m002, m003) — every one must surface.
    fk_tables = {
        "appointments",
        "daily_progress_snapshots",
        "engagement_events",
        "job_applications",
        "outcomes_records",
        "plan_history",
        "reminder_cooldowns",
        "resume_versions",
        "worker_unavailability",
    }
    # m001 session-keyed but no-FK tables.
    legacy_tables = {
        "feedback_tokens",
        "record_profiles",
        "resource_feedback",
        "share_tokens",
        "visit_feedback",
    }
    expected = fk_tables | legacy_tables
    assert expected.issubset(scoped), (
        f"introspection missing tables: {expected - scoped}"
    )


def test_seed_helper_plants_one_row_per_session_scoped_table(
    cascade_db: str,
) -> None:
    """Every introspected table reports >=1 row before any deletion."""
    conn = sqlite3.connect(cascade_db)
    try:
        for table in _session_scoped_tables(conn):
            cnt = _count_for_session(conn, table, _SESSION_ID)
            assert cnt >= 1, (
                f"{table!r} has no seeded row for session {_SESSION_ID!r} "
                "— seed helper missing or broken."
            )
    finally:
        conn.close()


# --------------------------------------------------------------- cascade

def test_full_delete_clears_every_session_scoped_table(
    cascade_db: str,
) -> None:
    """``full_delete`` must leave 0 rows in every session-scoped table."""
    from app.modules.compliance import delete as delete_mod

    # Pre-assert: rows present everywhere we expect to clear.
    conn = sqlite3.connect(cascade_db)
    try:
        scoped = _session_scoped_tables(conn)
        for table in scoped:
            assert _count_for_session(conn, table, _SESSION_ID) >= 1, (
                f"pre-assert: {table} not seeded"
            )
    finally:
        conn.close()

    delete_mod.full_delete(
        _SESSION_ID,
        db_path=cascade_db,
        reason="cascade-verification",
        actor_token="t13.70-test",
        now=_NOW,
    )

    # Post-assert: every introspected table has 0 rows for the deleted
    # session id; allowlisted tables are exempt by design.
    conn = sqlite3.connect(cascade_db)
    try:
        for table in scoped:
            if table in _RETAIN_ALLOWLIST:
                continue
            cnt = _count_for_session(conn, table, _SESSION_ID)
            assert cnt == 0, (
                f"full_delete left {cnt} rows in {table!r} for session "
                f"{_SESSION_ID!r} — add the table to delete.py's "
                "_NON_CASCADING_TABLES or declare ON DELETE CASCADE on "
                "its session_id FK."
            )
        # Sessions row itself is gone too.
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE id = ?", (_SESSION_ID,),
        ).fetchone()
        assert row is None, "sessions row survived full_delete"
    finally:
        conn.close()


def test_compliance_audit_row_retained_after_full_delete(
    cascade_db: str,
) -> None:
    """Audit row must persist (allowlist invariant)."""
    from app.modules.compliance import delete as delete_mod

    delete_mod.full_delete(
        _SESSION_ID,
        db_path=cascade_db,
        reason="cascade-verification",
        actor_token="t13.70-test",
        now=_NOW,
    )

    conn = sqlite3.connect(cascade_db)
    try:
        rows = conn.execute(
            "SELECT action FROM compliance_audit"
        ).fetchall()
    finally:
        conn.close()
    actions = [r[0] for r in rows]
    assert "full_delete" in actions, (
        f"compliance_audit lost the full_delete row (actions={actions!r})"
    )


# --------------------------------------------------------------- drift guard

def test_every_session_scoped_table_is_covered_or_allowlisted(
    cascade_db: str,
) -> None:
    """Schema-drift guard: every introspected table is accounted for.

    A table is "accounted for" when it is one of:

    * declared with ``ON DELETE CASCADE`` -> sessions(id) (rides the
      implicit cascade), OR
    * present in ``delete._NON_CASCADING_TABLES`` (explicitly DELETEd
      before the sessions row drops), OR
    * present in :data:`_RETAIN_ALLOWLIST` (intentionally retained).

    Any other table reaching the cascade-test fixture means a future
    migration introduced a session-scoped table without wiring it
    into ``full_delete`` — fail loudly with the offending name so the
    review-stage dev knows exactly what to fix.
    """
    from app.modules.compliance import delete as delete_mod

    conn = sqlite3.connect(cascade_db)
    try:
        fk_tables = set(_tables_with_fk_to_sessions(conn))
        scoped = set(_session_scoped_tables(conn))
    finally:
        conn.close()

    explicit = set(delete_mod._NON_CASCADING_TABLES)
    allowlisted = set(_RETAIN_ALLOWLIST)

    uncovered = scoped - fk_tables - explicit - allowlisted
    assert not uncovered, (
        "Session-scoped tables not covered by full_delete cascade: "
        f"{sorted(uncovered)!r}. Either declare ON DELETE CASCADE on "
        "the FK, add the table name to "
        "app.modules.compliance.delete._NON_CASCADING_TABLES, or add "
        "it to _RETAIN_ALLOWLIST in this test with a documented reason."
    )


def test_allowlist_entries_have_documented_reasons() -> None:
    """Defensive: every allowlist entry must come with a non-empty reason."""
    for table, reason in _RETAIN_ALLOWLIST.items():
        assert reason and len(reason) > 10, (
            f"Allowlist entry {table!r} missing a meaningful reason"
        )
