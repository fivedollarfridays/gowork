"""Tests verifying alembic revisions produce a schema byte-equivalent to the
legacy ``runner.apply_pending`` chain (m001..m010).

The acceptance criterion for T22.3 is "schema byte-equivalent on a fresh
sqlite DB". We achieve that by:

1. Running ``runner.apply_pending`` on a fresh sqlite file -> dump schema.
2. Running ``alembic upgrade head`` on a fresh sqlite file -> dump schema.
3. Diffing the sorted ``.schema`` outputs.

Both DBs are normalized for comparison: the alembic-version tracking table
(``alembic_version``) is stripped from the alembic side, and the legacy
``schema_migrations`` table is stripped from the runner side, so we compare
only the application schema produced by the migrations.
"""

from __future__ import annotations

import os
import re
import sqlite3
import subprocess
from pathlib import Path

import pytest

from app.core.migrations import runner

# Lines that are migration-tooling internal (not part of the application
# schema) — stripped from both sides before comparing.
_TOOLING_TABLE_PATTERNS = (
    re.compile(r"CREATE TABLE schema_migrations\b", re.IGNORECASE),
    re.compile(r"CREATE TABLE alembic_version\b", re.IGNORECASE),
    re.compile(r"CREATE INDEX [^ ]*alembic_version", re.IGNORECASE),
    # sqlite_sequence is auto-managed by sqlite when AUTOINCREMENT is
    # used; its presence depends on whether any AUTOINCREMENT-bearing
    # table has had a row inserted, not on the schema itself.
    re.compile(r"CREATE TABLE sqlite_sequence\b", re.IGNORECASE),
    # Identity-layer tables (T22.5, alembic 0011) have no legacy m*.py
    # counterpart — the legacy chain stops at m010. Strip them from the
    # alembic side so the parity check still pins the m001..m010 schema.
    re.compile(r"CREATE TABLE accounts\b", re.IGNORECASE),
    re.compile(r"CREATE TABLE account_sessions\b", re.IGNORECASE),
    re.compile(r"CREATE TABLE account_credentials\b", re.IGNORECASE),
    re.compile(
        r"CREATE INDEX [^ ]*idx_account_credentials_lookup",
        re.IGNORECASE,
    ),
    # Role-layer table (T22.6, alembic 0012) likewise has no legacy
    # m*.py counterpart — strip from the alembic side.
    re.compile(r"CREATE TABLE account_roles\b", re.IGNORECASE),
)


def _dump_app_schema(db_path: str) -> list[str]:
    """Return sorted application-level CREATE statements from a sqlite DB."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE sql IS NOT NULL "
            "ORDER BY type, name"
        ).fetchall()
    finally:
        conn.close()
    statements: list[str] = []
    for (sql,) in rows:
        if any(p.search(sql) for p in _TOOLING_TABLE_PATTERNS):
            continue
        # Normalize whitespace so "CREATE TABLE x(\n  ...\n)" matches
        # "CREATE TABLE x (\n  ...\n)" — alembic's op.execute preserves
        # the SQL text but sqlite normalises slightly on storage.
        normalized = re.sub(r"\s+", " ", sql).strip()
        statements.append(normalized)
    statements.sort()
    return statements


def _backend_dir() -> Path:
    """Return the absolute path to the backend dir (alembic root)."""
    return Path(__file__).resolve().parent.parent


def _run_alembic_upgrade(db_path: str) -> None:
    """Run ``alembic upgrade head`` against a sqlite file at db_path."""
    backend = _backend_dir()
    alembic_bin = backend / ".venv" / "bin" / "alembic"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    subprocess.run(
        [str(alembic_bin), "upgrade", "head"],
        cwd=str(backend),
        env=env,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def alembic_available() -> bool:
    """Skip parity tests when the alembic binary isn't reachable."""
    backend = _backend_dir()
    alembic_bin = backend / ".venv" / "bin" / "alembic"
    if not alembic_bin.exists():
        pytest.skip("alembic binary not found in backend/.venv")
    if not (backend / "alembic" / "versions").exists():
        pytest.skip("alembic versions/ dir missing")
    return True


def test_alembic_upgrade_head_matches_runner_schema(
    tmp_path, alembic_available
):
    """Alembic upgrade head must produce the same schema as runner.apply_pending."""
    legacy_db = str(tmp_path / "legacy.db")
    alembic_db = str(tmp_path / "alembic.db")

    runner.apply_pending(legacy_db)
    _run_alembic_upgrade(alembic_db)

    legacy_schema = _dump_app_schema(legacy_db)
    alembic_schema = _dump_app_schema(alembic_db)

    # Diagnostic when they diverge — show the symmetric difference.
    if legacy_schema != alembic_schema:
        only_legacy = set(legacy_schema) - set(alembic_schema)
        only_alembic = set(alembic_schema) - set(legacy_schema)
        msg_parts = ["Schema mismatch:"]
        if only_legacy:
            msg_parts.append("Only in legacy:")
            msg_parts.extend(f"  {s}" for s in sorted(only_legacy))
        if only_alembic:
            msg_parts.append("Only in alembic:")
            msg_parts.extend(f"  {s}" for s in sorted(only_alembic))
        pytest.fail("\n".join(msg_parts))


def test_alembic_revisions_chain_is_linear(alembic_available):
    """Each revision 0001..0012 must declare the previous as down_revision."""
    versions_dir = _backend_dir() / "alembic" / "versions"
    expected = {
        "0001": None,
        "0002": "0001",
        "0003": "0002",
        "0004": "0003",
        "0005": "0004",
        "0006": "0005",
        "0007": "0006",
        "0008": "0007",
        "0009": "0008",
        "0010": "0009",
        "0011": "0010",
        "0012": "0011",
    }
    files = sorted(versions_dir.glob("[0-9][0-9][0-9][0-9]_*.py"))
    assert len(files) == 12, f"expected 12 revisions, found {len(files)}"

    for path in files:
        rev = path.name[:4]
        text = path.read_text()
        rev_match = re.search(
            r"^revision:\s*(?:str\s*)?=\s*['\"]([^'\"]+)['\"]", text, re.M
        )
        down_match = re.search(
            r"^down_revision:[^=]*=\s*(None|['\"]([^'\"]+)['\"])",
            text,
            re.M,
        )
        assert rev_match, f"{path.name} missing revision = '...'"
        assert down_match, f"{path.name} missing down_revision = ..."
        assert rev_match.group(1) == rev, (
            f"{path.name} revision={rev_match.group(1)!r} != prefix {rev!r}"
        )
        if expected[rev] is None:
            assert down_match.group(1) == "None", (
                f"{path.name}: 0001 must have down_revision=None"
            )
        else:
            assert down_match.group(2) == expected[rev], (
                f"{path.name} down_revision={down_match.group(2)!r}, "
                f"expected {expected[rev]!r}"
            )


def test_runner_emits_deprecation_warning(tmp_path):
    """runner.apply_pending must emit a DeprecationWarning on call."""
    db_path = str(tmp_path / "warn.db")
    with pytest.warns(DeprecationWarning, match="alembic"):
        runner.apply_pending(db_path)
