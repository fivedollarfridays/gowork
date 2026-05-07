"""Dialect-translation helpers for replaying legacy m00X DDL.

The legacy ``m001`` — ``m010`` migrations were authored against sqlite and
embed sqlite-specific syntax (notably ``INTEGER PRIMARY KEY AUTOINCREMENT``).
When the alembic ports replay them on postgres, those statements need to be
translated. This module is the single seam where that translation lives — so
adding postgres support to a new sqlite-ism is one edit, not ten.

Usage::

    from alembic import op
    from app.core.migrations.m001_initial import DDL_SQL as _DDL
    from .._legacy_ddl import split_and_translate

    bind = op.get_bind()
    for stmt in split_and_translate(_DDL, bind.dialect.name):
        bind.exec_driver_sql(stmt)

The translator is a no-op on sqlite (sqlite is the source dialect), so the
byte-for-byte parity test against the legacy runner stays intact.
"""

from __future__ import annotations

import re
from typing import Iterator

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
