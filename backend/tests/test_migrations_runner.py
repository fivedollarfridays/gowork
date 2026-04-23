"""Tests for the migration runner infrastructure (T12.0).

Covers:
- Fresh DB: apply_pending creates schema_migrations + m001 tables
- Existing DB without schema_migrations: runner detects and applies
- Idempotency: second apply_pending returns empty list
- Rollback: --rollback 0 invokes downgrade
- schema_migrations table integrity
- Byte-for-byte DDL equivalence with legacy DDL_SQL
- Dry-run: prints SQL without executing
"""

import io
import sqlite3
from contextlib import redirect_stdout

from app.core.migrations import m001_initial, runner


# -------------------- Cycle 1: Fresh DB application --------------------


def test_apply_pending_fresh_db_returns_m001(tmp_path):
    """Fresh DB: apply_pending returns list containing 'm001_initial'."""
    db_path = str(tmp_path / "fresh.db")
    applied = runner.apply_pending(db_path)
    assert "m001_initial" in applied
    # m001 must be first (runner applies in version order)
    assert applied[0] == "m001_initial"


def test_apply_pending_creates_schema_migrations_table(tmp_path):
    """apply_pending creates schema_migrations tracking table."""
    db_path = str(tmp_path / "fresh.db")
    runner.apply_pending(db_path)
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        assert row is not None
    finally:
        conn.close()


def test_apply_pending_creates_m001_tables(tmp_path):
    """apply_pending m001 creates core application tables."""
    db_path = str(tmp_path / "fresh.db")
    runner.apply_pending(db_path)
    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        expected = {
            "employers", "transit_routes", "transit_stops", "resources",
            "job_listings", "sessions", "feedback_tokens", "visit_feedback",
            "resource_feedback", "barriers", "barrier_relationships",
            "barrier_resources", "employer_policies", "record_profiles",
            "share_tokens",
        }
        assert expected.issubset(tables)
    finally:
        conn.close()


# -------------------- Cycle 2: Idempotency + schema_migrations integrity --------------------


def test_apply_pending_second_run_returns_empty(tmp_path):
    """Re-running apply_pending returns empty list (idempotent)."""
    db_path = str(tmp_path / "fresh.db")
    runner.apply_pending(db_path)
    second = runner.apply_pending(db_path)
    assert second == []


def test_schema_migrations_integrity(tmp_path):
    """schema_migrations has version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL."""
    db_path = str(tmp_path / "fresh.db")
    runner.apply_pending(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cols = conn.execute("PRAGMA table_info(schema_migrations)").fetchall()
        # cols: [(cid, name, type, notnull, dflt_value, pk), ...]
        col_map = {row[1]: row for row in cols}
        assert "version" in col_map
        assert col_map["version"][2].upper() == "INTEGER"
        assert col_map["version"][5] == 1  # primary key
        assert "applied_at" in col_map
        assert col_map["applied_at"][2].upper() == "TEXT"
        assert col_map["applied_at"][3] == 1  # NOT NULL
    finally:
        conn.close()


def test_schema_migrations_row_recorded_for_m001(tmp_path):
    """After apply_pending, schema_migrations has a row for version 1."""
    db_path = str(tmp_path / "fresh.db")
    runner.apply_pending(db_path)
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT version, applied_at FROM schema_migrations"
        ).fetchall()
        versions = [r[0] for r in rows]
        assert 1 in versions
        # applied_at is non-empty string
        applied = [r[1] for r in rows if r[0] == 1][0]
        assert isinstance(applied, str) and len(applied) > 0
    finally:
        conn.close()


def test_existing_db_without_schema_migrations_applies_all(tmp_path):
    """DB created outside the runner gets schema_migrations + m001 on first run."""
    db_path = str(tmp_path / "preexisting.db")
    # Pre-create a DB with a stray table but no schema_migrations.
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    applied = runner.apply_pending(db_path)
    assert "m001_initial" in applied

    conn = sqlite3.connect(db_path)
    try:
        versions = [
            r[0]
            for r in conn.execute(
                "SELECT version FROM schema_migrations"
            ).fetchall()
        ]
        assert 1 in versions
    finally:
        conn.close()


# -------------------- Cycle 3: Rollback, dry-run, DDL equivalence --------------------


def test_rollback_invokes_m001_downgrade(tmp_path):
    """rollback to 0 drops m001 tables and removes its schema_migrations row."""
    db_path = str(tmp_path / "fresh.db")
    runner.apply_pending(db_path)

    runner.rollback(db_path, target_version=0)

    conn = sqlite3.connect(db_path)
    try:
        # m001 tables should be gone
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "employers" not in tables
        assert "resources" not in tables
        # schema_migrations row for version 1 is removed
        row = conn.execute(
            "SELECT version FROM schema_migrations WHERE version = 1"
        ).fetchone()
        assert row is None
    finally:
        conn.close()


def test_rollback_allows_reapplication(tmp_path):
    """After rollback, apply_pending re-applies m001."""
    db_path = str(tmp_path / "fresh.db")
    runner.apply_pending(db_path)
    runner.rollback(db_path, target_version=0)

    re_applied = runner.apply_pending(db_path)
    assert "m001_initial" in re_applied


def test_dry_run_does_not_execute(tmp_path):
    """Dry-run prints SQL but creates no tables and records no migration."""
    db_path = str(tmp_path / "dry.db")
    buf = io.StringIO()
    with redirect_stdout(buf):
        applied = runner.apply_pending(db_path, dry_run=True)
    output = buf.getvalue()

    # apply_pending reports what *would* be applied
    assert "m001_initial" in applied
    # SQL is printed (DDL fingerprint)
    assert "CREATE TABLE" in output

    # But the DB has no m001 tables
    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "employers" not in tables
        # schema_migrations either missing, or has no row for version 1
        if "schema_migrations" in tables:
            row = conn.execute(
                "SELECT COUNT(*) FROM schema_migrations WHERE version = 1"
            ).fetchone()
            assert row[0] == 0
    finally:
        conn.close()


def test_m001_upgrade_matches_legacy_ddl_sql_schema(tmp_path):
    """m001.upgrade(conn) produces the same table set as legacy DDL_SQL."""
    from app.core.schema import DDL_SQL

    # Schema from m001.upgrade
    db_new = str(tmp_path / "m001.db")
    conn_new = sqlite3.connect(db_new)
    m001_initial.upgrade(conn_new)
    conn_new.commit()
    new_schema = _dump_table_schemas(conn_new)
    conn_new.close()

    # Schema from legacy DDL_SQL blob
    db_legacy = str(tmp_path / "legacy.db")
    conn_legacy = sqlite3.connect(db_legacy)
    for stmt in DDL_SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn_legacy.execute(stmt)
    conn_legacy.commit()
    legacy_schema = _dump_table_schemas(conn_legacy)
    conn_legacy.close()

    assert new_schema == legacy_schema


def _dump_table_schemas(conn: sqlite3.Connection) -> dict[str, str]:
    """Return {table_name: normalized CREATE TABLE sql}. Excludes schema_migrations."""
    rows = conn.execute(
        "SELECT name, sql FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "AND name != 'schema_migrations'"
    ).fetchall()
    return {name: _normalize_sql(sql) for name, sql in rows if sql}


def _normalize_sql(sql: str) -> str:
    """Collapse whitespace so formatting differences don't fail equality."""
    return " ".join(sql.split())


# -------------------- Sanity: module shape matches ops convention --------------------


def test_m001_exports_schema_version_and_funcs():
    """m001 module exports SCHEMA_VERSION, upgrade, downgrade per ops convention."""
    assert hasattr(m001_initial, "SCHEMA_VERSION")
    assert m001_initial.SCHEMA_VERSION == 1
    assert callable(getattr(m001_initial, "upgrade", None))
    assert callable(getattr(m001_initial, "downgrade", None))


def test_schema_py_still_exports_ddl_sql():
    """Backward-compat: legacy DDL_SQL re-export still works for existing callers."""
    from app.core.schema import DDL_SQL

    assert isinstance(DDL_SQL, str)
    assert "CREATE TABLE" in DDL_SQL
