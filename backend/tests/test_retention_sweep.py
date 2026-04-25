"""Retention sweep verification (T13.58).

Goal
----
Lock in the invariants of :func:`app.modules.compliance.retention.retention_sweep`:

1. **Aged-session detection** — sessions whose ``expires_at`` is older than
   ``now - RETENTION_GRACE_DAYS`` are flagged for purge; everything within
   the window survives. The threshold is inclusive (``<=``) — a session
   that lands exactly on the boundary is purged.
2. **Cascade completeness** — the sweep clears every session-scoped row,
   not just the ones declared with ``ON DELETE CASCADE``. Verified by
   reusing the T13.70 introspection seed (every session-scoped table
   gets a row before the sweep, every one must have zero rows after).
3. **Audit preservation** — every purge writes one ``compliance_audit``
   row with ``action="retention_purge"`` and ``session_id_hash`` set to
   the SHA256 of the raw id (raw id is never persisted to the audit row).
4. **Orchestrator wiring** — the sweep fires once per nightly run,
   driven by the documented invocation in
   :mod:`scripts.nightly_digest`.
5. **No-op on empty** — when no session is past the grace window,
   the sweep returns an empty list and writes no audit rows.
6. **Idempotence** — running the sweep twice in a row leaves no stale
   side effects (the second invocation is a no-op).

Cascade gap surfaced by these tests
-----------------------------------
``retention_sweep`` only does ``DELETE FROM sessions``; the SQLite
cascade clears every m002 child (FK + ``ON DELETE CASCADE``) but does
NOT touch the m001 ``session_id``-but-no-FK tables that T13.70 already
fixed in :func:`compliance.delete.full_delete`. The cascade test below
fails until ``retention_sweep`` is taught to clear the same
``_NON_CASCADING_TABLES`` list.
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from app.modules.compliance import retention
from tests._fake_clock import freeze_time

# ---- Reuse the T13.70 introspection + per-table seed dispatch. ----
# This is the canonical "every session-scoped table" inventory; the
# retention sweep must clear the same surface area as full_delete.
from tests.test_compliance_cascade import (
    _NOW as _CASCADE_NOW,
    _RETAIN_ALLOWLIST,
    _SEEDERS,
    _count_for_session,
    _session_scoped_tables,
)

# --------------------------------------------------------------- constants

# Frozen reference instant: keeps the test deterministic across DST and
# leap-second weirdness. Aligns with the cascade-test clock so seeded
# child rows from ``_SEEDERS`` (which use ``_CASCADE_NOW``) are
# consistent with the sweep's ``now`` parameter.
_NOW = _CASCADE_NOW
_GRACE = retention.RETENTION_GRACE_DAYS  # 90 days


# --------------------------------------------------------------- fixtures

@pytest.fixture
def migrated_db(tmp_path: Path) -> str:
    """Fresh DB with the full migration chain (through m007)."""
    db_path = str(tmp_path / "retention.db")
    runner.apply_pending(db_path)
    return db_path


# --------------------------------------------------------------- seed helpers

def _seed_session(
    db_path: str, session_id: str, *, expires_at: datetime,
) -> None:
    """Insert a minimal ``sessions`` row with the given ``expires_at``."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, _NOW.isoformat(), "[]", expires_at.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def _surviving_session_ids(db_path: str) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT id FROM sessions").fetchall()
    finally:
        conn.close()
    return {r[0] for r in rows}


def _audit_actions(db_path: str) -> list[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT action FROM compliance_audit ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def _audit_rows_for(db_path: str, action: str) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM compliance_audit WHERE action = ?", (action,),
        ).fetchall()
    finally:
        conn.close()
    return rows


def _seed_aged_session_with_full_cascade(
    db_path: str, sid: str, *, expires_at: datetime,
) -> list[str]:
    """Plant the parent ``sessions`` row + one row per session-scoped table.

    Reuses the T13.70 ``_SEEDERS`` dispatch so the cascade test exercises
    the same surface area that ``test_full_delete_clears_every_session_scoped_table``
    locks in. Returns the list of session-scoped tables seeded so the
    caller can iterate the same set in the post-assert.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (sid, _NOW.isoformat(), "[]", expires_at.isoformat()),
        )
        scoped_tables = _session_scoped_tables(conn)
        for table in scoped_tables:
            seeder = _SEEDERS.get(table)
            assert seeder is not None, (
                f"no seed helper for session-scoped table {table!r}; "
                "extend the T13.70 _SEEDERS dispatch"
            )
            seeder(conn, sid)
        conn.commit()
    finally:
        conn.close()
    return scoped_tables


def _assert_every_table_seeded(
    db_path: str, sid: str, scoped_tables: list[str],
) -> None:
    """Pre-assert: every introspected table has the seeded row."""
    conn = sqlite3.connect(db_path)
    try:
        for table in scoped_tables:
            assert _count_for_session(conn, table, sid) >= 1, (
                f"pre-assert: {table!r} missing seeded row"
            )
    finally:
        conn.close()


def _assert_every_table_cleared(
    db_path: str, sid: str, scoped_tables: list[str],
) -> None:
    """Post-assert: every non-allowlisted table is empty for ``sid``."""
    conn = sqlite3.connect(db_path)
    try:
        for table in scoped_tables:
            if table in _RETAIN_ALLOWLIST:
                continue
            cnt = _count_for_session(conn, table, sid)
            assert cnt == 0, (
                f"retention_sweep left {cnt} rows in {table!r} for purged "
                f"session {sid!r}; cascade gap — extend the sweep to "
                "cover the same surface area as full_delete "
                "(see _NON_CASCADING_TABLES)."
            )
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE id = ?", (sid,),
        ).fetchone()
        assert row is None, "sessions row survived retention_sweep"
    finally:
        conn.close()


# --------------------------------------------------------------- aged-session detection

def test_aged_session_detected(migrated_db: str) -> None:
    """A session past ``expires_at + grace`` is purged."""
    aged = _NOW - timedelta(days=_GRACE + 1)
    _seed_session(migrated_db, "sess-aged", expires_at=aged)

    purged = retention.retention_sweep(db_path=migrated_db, now=_NOW)

    assert purged == ["sess-aged"]
    assert "sess-aged" not in _surviving_session_ids(migrated_db)


def test_fresh_session_preserved(migrated_db: str) -> None:
    """A session whose ``expires_at`` is still in the future is untouched."""
    fresh = _NOW + timedelta(days=30)
    _seed_session(migrated_db, "sess-fresh", expires_at=fresh)

    purged = retention.retention_sweep(db_path=migrated_db, now=_NOW)

    assert purged == []
    assert "sess-fresh" in _surviving_session_ids(migrated_db)


def test_session_within_grace_window_preserved(migrated_db: str) -> None:
    """A session expired but inside the 90-day grace window survives."""
    grace = _NOW - timedelta(days=_GRACE - 1)
    _seed_session(migrated_db, "sess-grace", expires_at=grace)

    purged = retention.retention_sweep(db_path=migrated_db, now=_NOW)

    assert purged == []
    assert "sess-grace" in _surviving_session_ids(migrated_db)


def test_session_exactly_on_boundary_is_purged(migrated_db: str) -> None:
    """Boundary case: ``expires_at == now - grace`` is at the cutoff (``<=``)."""
    boundary = _NOW - timedelta(days=_GRACE)
    _seed_session(migrated_db, "sess-boundary", expires_at=boundary)

    purged = retention.retention_sweep(db_path=migrated_db, now=_NOW)

    # Implementation uses ``<=`` so the boundary IS purged. Locks in the
    # current contract — flipping the comparator is a behaviour change
    # that requires updating this assertion deliberately.
    assert "sess-boundary" in purged


def test_mixed_ages_only_aged_purged(migrated_db: str) -> None:
    """Mix of aged + grace + fresh: only the aged one is purged."""
    _seed_session(
        migrated_db, "sess-aged",
        expires_at=_NOW - timedelta(days=_GRACE + 10),
    )
    _seed_session(
        migrated_db, "sess-grace",
        expires_at=_NOW - timedelta(days=_GRACE - 10),
    )
    _seed_session(
        migrated_db, "sess-fresh",
        expires_at=_NOW + timedelta(days=10),
    )

    purged = retention.retention_sweep(db_path=migrated_db, now=_NOW)

    assert purged == ["sess-aged"]
    survivors = _surviving_session_ids(migrated_db)
    assert "sess-aged" not in survivors
    assert "sess-grace" in survivors
    assert "sess-fresh" in survivors


# --------------------------------------------------------------- cascade

def test_sweep_cascades_through_session_scoped_tables(
    migrated_db: str,
) -> None:
    """The sweep clears every session-scoped table for the purged session.

    Reuses the T13.70 introspection seed (via the helper above): one row
    per session-scoped table. After the sweep, every non-allowlisted
    table must report zero rows for the purged session id.
    ``compliance_audit`` is the one allowlisted survivor (it stores
    ``session_id_hash``, not the raw id, and the sweep itself writes
    one of these rows).
    """
    sid = "sess-aged-cascade"
    aged = _NOW - timedelta(days=_GRACE + 1)
    scoped = _seed_aged_session_with_full_cascade(
        migrated_db, sid, expires_at=aged,
    )
    _assert_every_table_seeded(migrated_db, sid, scoped)

    purged = retention.retention_sweep(db_path=migrated_db, now=_NOW)

    assert purged == [sid]
    _assert_every_table_cleared(migrated_db, sid, scoped)


# --------------------------------------------------------------- audit

def test_sweep_audit_row_written(migrated_db: str) -> None:
    """One ``retention_purge`` audit row per purge, with hashed session id."""
    sid = "sess-aged-audit"
    aged = _NOW - timedelta(days=_GRACE + 5)
    _seed_session(migrated_db, sid, expires_at=aged)

    retention.retention_sweep(db_path=migrated_db, now=_NOW)

    rows = _audit_rows_for(migrated_db, "retention_purge")
    assert len(rows) == 1, f"expected 1 retention_purge row, got {len(rows)}"
    row = rows[0]
    expected_hash = hashlib.sha256(sid.encode("utf-8")).hexdigest()
    assert row["session_id_hash"] == expected_hash, (
        "audit row must store sha256(session_id), never the raw id"
    )
    # Defensive: raw id MUST NOT appear anywhere in the audit row, even
    # in the payload JSON. Walk every column.
    for key in row.keys():
        value = row[key]
        if isinstance(value, str):
            assert sid not in value, (
                f"raw session id leaked into compliance_audit.{key}"
            )


def test_sweep_audit_one_row_per_purged_session(migrated_db: str) -> None:
    """N purges => N ``retention_purge`` audit rows (one each)."""
    aged = _NOW - timedelta(days=_GRACE + 1)
    sids = ["sess-a", "sess-b", "sess-c"]
    for sid in sids:
        _seed_session(migrated_db, sid, expires_at=aged)

    retention.retention_sweep(db_path=migrated_db, now=_NOW)

    rows = _audit_rows_for(migrated_db, "retention_purge")
    assert len(rows) == len(sids)
    hashes = {r["session_id_hash"] for r in rows}
    expected = {
        hashlib.sha256(s.encode("utf-8")).hexdigest() for s in sids
    }
    assert hashes == expected


# --------------------------------------------------------------- orchestrator wiring

def test_sweep_runs_on_schedule_via_orchestrator(
    migrated_db: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The nightly orchestrator invokes ``retention_sweep`` once per run.

    Drives the public ``run_nightly_digest`` entrypoint with the fake
    clock pinned at the cron's documented fire instant (02:00 CT). We
    spy on ``retention.retention_sweep`` so the assertion holds even
    when no aged sessions are present. The orchestrator must call it
    exactly once per run regardless of how many cities (or sessions)
    are processed.
    """
    import scripts.nightly_digest as nd

    calls: list[dict] = []

    def _spy(*, db_path, now=None):
        calls.append({"db_path": str(db_path), "now": now})
        return []

    # The orchestrator imports the module as ``_retention_mod`` and
    # invokes ``_retention_mod.retention_sweep`` — patching the same
    # attr on that module is the only path that intercepts the call.
    monkeypatch.setattr(nd._retention_mod, "retention_sweep", _spy)

    # Seed a session for the cities we'll process — the orchestrator
    # bails out per-city if there are no sessions, but retention runs
    # AFTER the city loop regardless.
    fire_at = datetime(2026, 4, 24, 7, 0, tzinfo=timezone.utc)  # 02:00 CT
    import asyncio

    with freeze_time(fire_at):
        asyncio.run(
            nd.run_nightly_digest(
                cities=["montgomery"], db_path=migrated_db, now=fire_at,
            )
        )

    assert len(calls) == 1, (
        f"orchestrator should call retention_sweep exactly once per "
        f"nightly run; got {len(calls)} calls"
    )
    assert calls[0]["now"] == fire_at, (
        "orchestrator must forward its own ``now`` to the sweep so the "
        "cutoff is computed against the same instant as the rest of "
        "the run"
    )


# --------------------------------------------------------------- edge cases

def test_sweep_handles_zero_aged_sessions(migrated_db: str) -> None:
    """Empty case: no aged sessions => no purges, no audit rows, no errors."""
    _seed_session(
        migrated_db, "sess-fresh-1",
        expires_at=_NOW + timedelta(days=10),
    )
    _seed_session(
        migrated_db, "sess-fresh-2",
        expires_at=_NOW - timedelta(days=_GRACE - 1),  # within grace
    )

    purged = retention.retention_sweep(db_path=migrated_db, now=_NOW)

    assert purged == []
    # No audit rows whatsoever — the sweep does not record "nothing happened".
    assert _audit_actions(migrated_db) == []


def test_sweep_idempotent(migrated_db: str) -> None:
    """Running the sweep twice in a row: second run is a no-op."""
    sid = "sess-aged-idem"
    aged = _NOW - timedelta(days=_GRACE + 5)
    _seed_session(migrated_db, sid, expires_at=aged)

    first = retention.retention_sweep(db_path=migrated_db, now=_NOW)
    second = retention.retention_sweep(db_path=migrated_db, now=_NOW)

    assert first == [sid]
    assert second == [], (
        "second sweep must be a no-op (the session is already purged)"
    )
    # Only one audit row — the second run found nothing to record.
    rows = _audit_rows_for(migrated_db, "retention_purge")
    assert len(rows) == 1


def test_sweep_empty_database_is_no_op(migrated_db: str) -> None:
    """No sessions at all: sweep returns empty, writes nothing, no errors."""
    purged = retention.retention_sweep(db_path=migrated_db, now=_NOW)

    assert purged == []
    assert _audit_actions(migrated_db) == []
