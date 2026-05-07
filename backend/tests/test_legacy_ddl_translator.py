"""Unit tests for the legacy DDL dialect translator.

The translator is the seam where sqlite-authored DDL (m001-m010) gets
rewritten for postgres at alembic-replay time. Without this layer,
``INTEGER PRIMARY KEY AUTOINCREMENT`` causes ``syntax error at or near
"AUTOINCREMENT"`` on postgres.
"""

from __future__ import annotations

from app.core.migrations.legacy_ddl_translator import (
    split_and_translate,
    translate_for_dialect,
)


def test_sqlite_passthrough_preserves_autoincrement():
    """Sqlite is the source dialect — translator must not touch the SQL."""
    stmt = "CREATE TABLE foo (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    assert translate_for_dialect(stmt, "sqlite") == stmt


def test_postgres_replaces_autoincrement_with_serial():
    """Postgres has no AUTOINCREMENT — substitute SERIAL PRIMARY KEY."""
    stmt = "CREATE TABLE foo (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    out = translate_for_dialect(stmt, "postgresql")
    assert "AUTOINCREMENT" not in out
    assert "SERIAL PRIMARY KEY" in out
    assert "INTEGER PRIMARY KEY" not in out


def test_postgres_substitution_handles_extra_whitespace():
    """Match should be tolerant to multiple spaces / tabs in the legacy DDL."""
    stmt = "CREATE TABLE foo (id  INTEGER   PRIMARY  KEY    AUTOINCREMENT)"
    out = translate_for_dialect(stmt, "postgresql")
    assert "AUTOINCREMENT" not in out
    assert "SERIAL PRIMARY KEY" in out


def test_postgres_substitution_is_case_insensitive():
    """Legacy DDL mixes case in places (autoincrement vs AUTOINCREMENT)."""
    stmt = "CREATE TABLE foo (id integer primary key autoincrement)"
    out = translate_for_dialect(stmt, "postgresql")
    assert "autoincrement" not in out.lower()


def test_unknown_dialect_passthrough():
    """Unknown dialect — no translation. Caller is responsible."""
    stmt = "CREATE TABLE foo (id INTEGER PRIMARY KEY AUTOINCREMENT)"
    assert translate_for_dialect(stmt, "mysql") == stmt


def test_split_and_translate_filters_empty_statements():
    """Trailing semicolons must not produce empty fragments."""
    blob = "CREATE TABLE a (x INT);;CREATE TABLE b (y INT);"
    stmts = list(split_and_translate(blob, "sqlite"))
    assert stmts == ["CREATE TABLE a (x INT)", "CREATE TABLE b (y INT)"]


def test_split_and_translate_translates_each_statement():
    """Each split statement runs through the translator."""
    blob = (
        "CREATE TABLE a (id INTEGER PRIMARY KEY AUTOINCREMENT);"
        "CREATE TABLE b (id INTEGER PRIMARY KEY AUTOINCREMENT)"
    )
    stmts = list(split_and_translate(blob, "postgresql"))
    assert len(stmts) == 2
    for stmt in stmts:
        assert "AUTOINCREMENT" not in stmt
        assert "SERIAL PRIMARY KEY" in stmt
