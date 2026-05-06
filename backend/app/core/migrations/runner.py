"""Migration runner — discovers m*.py modules, applies pending versions in order.

DEPRECATED (T22.3): The legacy m*.py runner remains callable for backward
compatibility (50+ tests use it directly), but new callers should use
``alembic upgrade head`` instead. The Alembic versions in
``backend/alembic/versions/`` produce a byte-equivalent schema and are the
authoritative source going forward. ``apply_pending`` emits a
``DeprecationWarning`` on every invocation; the underlying logic is
unchanged so existing callsites continue to work without disruption.

Pattern mirrors ops:lib/db.py (`_ensure_schema`, `_current_version`,
`_apply_migrations`) but adapted to stdlib sqlite3 + glob-based discovery so
new migrations drop in without editing the runner.

Tracking table:
    schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)
"""

from __future__ import annotations

import glob
import importlib
import os
import re
import sqlite3
import warnings
from types import ModuleType
from typing import Iterable

_MIGRATION_PREFIX_RE = re.compile(r"^m(\d+)_")
_PACKAGE = "app.core.migrations"
_TRACKING_DDL = (
    "CREATE TABLE IF NOT EXISTS schema_migrations ("
    "version INTEGER PRIMARY KEY, "
    "applied_at TEXT NOT NULL"
    ")"
)
_DEPRECATION_MESSAGE = (
    "app.core.migrations.runner.apply_pending is deprecated; use "
    "`alembic upgrade head` instead. The Alembic versions in "
    "backend/alembic/versions/ are now the authoritative migration chain."
)


def apply_pending(db_path: str, dry_run: bool = False) -> list[str]:
    """Apply all pending migrations in version order.

    Returns the list of migration module names applied (or that would be
    applied under dry_run). Empty list when DB is already up-to-date.

    .. deprecated:: T22.3
       Use ``alembic upgrade head`` instead. Behaviour unchanged for
       backward compatibility; emits ``DeprecationWarning`` on call.
    """
    warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)
    migrations = _discover_migrations()
    if dry_run:
        return _dry_run(db_path, migrations)

    os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        _ensure_tracking_table(conn)
        applied_versions = _current_versions(conn)
        applied_names: list[str] = []
        for version, name, module in migrations:
            if version in applied_versions:
                continue
            module.upgrade(conn)
            _record_applied(conn, version)
            applied_names.append(name)
        conn.commit()
        return applied_names
    finally:
        conn.close()


def rollback(db_path: str, target_version: int) -> list[str]:
    """Roll back migrations with version > target_version, newest first.

    Returns the list of migration module names rolled back.
    """
    migrations = _discover_migrations()
    conn = sqlite3.connect(db_path)
    try:
        _ensure_tracking_table(conn)
        applied_versions = _current_versions(conn)
        rolled_back: list[str] = []
        for version, name, module in reversed(migrations):
            if version <= target_version:
                continue
            if version not in applied_versions:
                continue
            module.downgrade(conn)
            _remove_version(conn, version)
            rolled_back.append(name)
        conn.commit()
        return rolled_back
    finally:
        conn.close()


def _dry_run(db_path: str, migrations: list[tuple[int, str, ModuleType]]) -> list[str]:
    """Print SQL without executing; report which migrations would run."""
    applied_versions: set[int] = set()
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            if _tracking_table_exists(conn):
                applied_versions = _current_versions(conn)
        finally:
            conn.close()

    would_apply: list[str] = []
    for version, name, module in migrations:
        if version in applied_versions:
            continue
        would_apply.append(name)
        print(f"-- {name} (version {version})")
        ddl = getattr(module, "DDL_SQL", None)
        if ddl:
            print(ddl)
        else:
            print(f"-- (upgrade handler: {module.__name__}.upgrade)")
    return would_apply


def _discover_migrations() -> list[tuple[int, str, ModuleType]]:
    """Return [(version, module_name, module), ...] sorted by version.

    Discovers any m{NNN}_*.py file alongside this runner, imports it, and
    reads SCHEMA_VERSION. Files without SCHEMA_VERSION are skipped.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = glob.glob(os.path.join(here, "m*.py"))
    found: list[tuple[int, str, ModuleType]] = []
    for path in candidates:
        name = os.path.splitext(os.path.basename(path))[0]
        if not _MIGRATION_PREFIX_RE.match(name):
            continue
        module = importlib.import_module(f"{_PACKAGE}.{name}")
        version = getattr(module, "SCHEMA_VERSION", None)
        if not isinstance(version, int):
            continue
        found.append((version, name, module))
    found.sort(key=lambda item: item[0])
    return found


def _ensure_tracking_table(conn: sqlite3.Connection) -> None:
    """Create schema_migrations tracking table if absent."""
    conn.execute(_TRACKING_DDL)
    conn.commit()


def _tracking_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='schema_migrations'"
    ).fetchone()
    return row is not None


def _current_versions(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def _record_applied(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO schema_migrations (version, applied_at) "
        "VALUES (?, datetime('now'))",
        (version,),
    )


def _remove_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))


# Keep Iterable import used so ruff doesn't flag it; retained for future
# signature extension (e.g. apply_pending(db_path, only: Iterable[int])).
_ = Iterable
