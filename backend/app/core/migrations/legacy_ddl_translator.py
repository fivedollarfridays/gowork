"""Dialect-translation + introspection helpers for legacy m00X DDL replay.

The legacy ``m001`` — ``m010`` migrations were authored against sqlite and
embed sqlite-specific syntax (notably ``INTEGER PRIMARY KEY AUTOINCREMENT``)
and dialect-specific introspection (``PRAGMA table_info`` /
``information_schema``). When the alembic ports replay them on postgres,
those statements need to be translated and the introspection needs to be
dialect-aware. This module is the single seam where that lives — so adding
postgres support to a new sqlite-ism is one edit, not ten.

Usage::

    from alembic import op
    from app.core.migrations.m001_initial import DDL_SQL as _DDL
    from app.core.migrations.legacy_ddl_translator import (
        split_and_translate, has_column,
    )

    bind = op.get_bind()
    for stmt in split_and_translate(_DDL, bind.dialect.name):
        bind.exec_driver_sql(stmt)
    if not has_column(bind, "sessions", "demo"):
        op.execute("ALTER TABLE sessions ADD COLUMN demo INTEGER DEFAULT 0")

The translator is a no-op on sqlite (sqlite is the source dialect), so the
byte-for-byte parity test against the legacy runner stays intact.
"""

from __future__ import annotations

import re
from typing import Iterator

from sqlalchemy import text

# Embedded-semicolon caveat: ``split_and_translate`` does a naive ``split(";")``.
# The legacy m001-m010 DDL has been audited and contains no semicolons inside
# string literals or CHECK constraints. Future migrations adding such patterns
# must extend the splitter (or use parameterised CHECK clauses).

# ``INTEGER PRIMARY KEY AUTOINCREMENT`` (sqlite) → ``SERIAL PRIMARY KEY``
# (postgres). Both produce auto-incrementing integer PKs; insert-without-id
# returns the new id via ``RETURNING id`` on both engines.
_AUTOINCREMENT_RE = re.compile(
    r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
    re.IGNORECASE,
)


def translate_for_dialect(stmt: str, dialect: str) -> str:
    """Translate a sqlite-authored DDL statement for the target dialect.

    Sqlite is the source dialect; passthrough.
    Postgres needs sqlite-specific syntax replaced. Currently handles
    AUTOINCREMENT; extend here as future migrations surface other dialect
    differences in CI.
    """
    if dialect == "sqlite":
        return stmt
    if dialect == "postgresql":
        return _AUTOINCREMENT_RE.sub("SERIAL PRIMARY KEY", stmt)
    return stmt


def split_and_translate(blob: str, dialect: str) -> Iterator[str]:
    """Split a multi-statement DDL blob and translate each for the dialect.

    Empty fragments from trailing semicolons are filtered out.
    """
    for raw in blob.split(";"):
        stmt = raw.strip()
        if not stmt:
            continue
        yield translate_for_dialect(stmt, dialect)


def has_table(bind, name: str) -> bool:
    """Dialect-aware table existence check.

    Replaces five copy-pasted inline checks across alembic versions.
    """
    if bind.dialect.name == "sqlite":
        row = bind.exec_driver_sql(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (name,),
        ).fetchone()
        return row is not None
    # Postgres / other — use information_schema with named bind so asyncpg
    # works. ``exec_driver_sql`` with ``%s`` is psycopg-style and rejected
    # by asyncpg's prepared-statement layer.
    row = bind.execute(
        text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :name"
        ),
        {"name": name},
    ).fetchone()
    return row is not None


def has_column(bind, table: str, column: str) -> bool:
    """Dialect-aware column existence check.

    Replaces five copy-pasted inline checks across alembic versions
    (0005, 0006, 0008, 0009, 0010).
    """
    if bind.dialect.name == "sqlite":
        # PRAGMA cannot take placeholders; ``table`` must come from a
        # trusted constant (it does — the callsites pass migration-defined
        # table names, never user input).
        rows = bind.exec_driver_sql(
            f"PRAGMA table_info({table})"
        ).fetchall()
        return any(row[1] == column for row in rows)
    row = bind.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    ).fetchone()
    return row is not None
