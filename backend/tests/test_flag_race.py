"""Feature-flag state-machine race tests (T13.64, S13).

The flag system at :mod:`app.core.feature_flags` resolves
``is_enabled`` via a four-stage chain (env > runtime override > YAML >
default). The runtime-override stage is an in-process dict
(``_RUNTIME_OVERRIDES``) guarded by a single :class:`threading.Lock`
(``_LOCK``); the audit row is written by ``set_flag_runtime`` to the
``feature_flag_audit`` table immediately after the dict update.

There is intentionally **no TTL cache** in this implementation — every
``is_enabled`` call dereferences the dict under the lock, so writes
become visible to subsequent reads in the same process the moment the
toggling thread releases ``_LOCK``. Cross-process consistency is
out-of-scope (overrides are in-memory; new processes start with the
YAML/env baseline only). This test suite pins those invariants:

* Every toggle writes exactly one audit row (no drops, no duplicates).
* Concurrent readers always see either the pre- or post-toggle value
  during a write, never a "torn" read or a wrong-typed response.
* Final dict state matches the last writer's value.
* Audit-row count under burst contention equals the toggle count.
* No TTL cache exists (reads always live; documented invariant).

Threading model: the FastAPI route is exercised through
``TestClient`` so the same code path the production admin endpoint
takes is hit (auth + rate-limit + audit), and reads are issued via the
public :func:`is_enabled` to avoid coupling tests to internals.
A ``threading.Barrier`` synchronizes the contending threads at the
boundary so the race window is maximally exposed under CPython's GIL.
"""

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import app.core.feature_flags as ff
from app.core.config import get_settings
from app.core.migrations import m001_initial, m002_s12_worker_companion

_ADMIN_KEY = "flag-race-admin-key-0123456789-abcdef"
_SETTINGS_PATCH = "app.core.auth.get_settings"
_FLAG = "TEST_RACE_FLAG"


# -------------------- Fixtures --------------------


def _mock_settings(db_path: Path) -> MagicMock:
    s = MagicMock()
    s.admin_api_key = _ADMIN_KEY
    s.database_url = f"sqlite+aiosqlite:///{db_path}"
    return s


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Fresh on-disk SQLite with m001 + m002 applied (gives feature_flag_audit)."""
    path = tmp_path / "flag_race.db"
    conn = sqlite3.connect(str(path))
    try:
        m001_initial.upgrade(conn)
        m002_s12_worker_companion.upgrade(conn)
        conn.commit()
    finally:
        conn.close()
    return path


@pytest.fixture
def reset_flag_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Wipe in-memory overrides + rate-limiter; point YAML at empty file."""
    yaml_path = tmp_path / "flags.yaml"
    yaml_path.write_text(f"{_FLAG}: false\n")
    monkeypatch.setattr(ff, "_YAML_PATH", yaml_path)
    monkeypatch.delenv(f"FEATURE_{_FLAG}", raising=False)
    ff._reset_state_for_tests()
    yield
    ff._reset_state_for_tests()


@pytest.fixture
def patched_settings(db_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Patch get_settings everywhere the flag stack reads it."""
    get_settings.cache_clear()
    stub = _mock_settings(db_path)
    monkeypatch.setattr(_SETTINGS_PATCH, lambda: stub)
    monkeypatch.setattr(
        "app.core.feature_flags.get_settings", lambda: stub, raising=False,
    )
    yield stub
    get_settings.cache_clear()


@pytest.fixture
def client(patched_settings, reset_flag_state) -> TestClient:
    """TestClient bound to the patched flag stack."""
    from app.main import app

    return TestClient(app)


# -------------------- Helpers --------------------


def _audit_count(db_path: Path, flag_name: str = _FLAG) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM feature_flag_audit WHERE flag_name = ?",
            (flag_name,),
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


def _audit_rows(db_path: Path, flag_name: str = _FLAG) -> list[tuple[Any, ...]]:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(
            "SELECT old_value, new_value, reason, timestamp "
            "FROM feature_flag_audit WHERE flag_name = ? ORDER BY id",
            (flag_name,),
        ).fetchall()
    finally:
        conn.close()


def _toggle_via_api(
    client: TestClient, enabled: bool, reason: str = "race-test",
) -> int:
    """Issue a single toggle; return the HTTP status code."""
    resp = client.post(
        f"/api/admin/flags/{_FLAG}",
        headers={"X-Admin-Key": _ADMIN_KEY},
        json={"enabled": enabled, "reason": reason},
    )
    return resp.status_code


# -------------------- Test 1: single toggle = 1 audit row --------------------


def test_single_toggle_writes_one_audit_row(
    client: TestClient, db_path: Path,
) -> None:
    """Sanity: one POST → flag flipped + exactly one audit row."""
    assert ff.is_enabled(_FLAG) is False
    assert _audit_count(db_path) == 0

    status = _toggle_via_api(client, enabled=True, reason="single-toggle")
    assert status == 200

    assert ff.is_enabled(_FLAG) is True
    assert _audit_count(db_path) == 1

    rows = _audit_rows(db_path)
    assert rows[0][:3] == ("false", "true", "single-toggle")


# -------------------- Test 2: 100 readers + 1 toggler --------------------


def test_concurrent_reads_consistent_during_toggle(
    client: TestClient, db_path: Path,
) -> None:
    """100 concurrent readers must always observe a valid bool, never garbage.

    Final state matches the toggler's intent. The tolerated read values
    are exactly {pre-toggle, post-toggle}. No reader returns ``None``,
    raises, or yields a non-bool.
    """
    assert ff.is_enabled(_FLAG) is False  # baseline

    n_readers = 100
    barrier = threading.Barrier(n_readers + 1)
    read_results: list[Any] = []
    read_lock = threading.Lock()

    def _reader() -> None:
        barrier.wait(timeout=10.0)
        # Spin a few times so readers overlap the toggle.
        for _ in range(5):
            value = ff.is_enabled(_FLAG)
            with read_lock:
                read_results.append(value)

    def _toggler() -> int:
        barrier.wait(timeout=10.0)
        return _toggle_via_api(client, enabled=True, reason="reader-toggle-race")

    with ThreadPoolExecutor(max_workers=n_readers + 1) as pool:
        reader_futs = [pool.submit(_reader) for _ in range(n_readers)]
        toggler_fut = pool.submit(_toggler)
        for f in reader_futs:
            f.result(timeout=10.0)
        assert toggler_fut.result(timeout=10.0) == 200

    # Every read result is a real bool, never None or a torn value.
    assert all(isinstance(v, bool) for v in read_results), (
        f"non-bool read observed: {set(type(v).__name__ for v in read_results)}"
    )
    # Every read is one of the two valid values for this race.
    assert set(read_results) <= {False, True}
    # Final dict state is the writer's intent.
    assert ff.is_enabled(_FLAG) is True
    # And exactly one audit row was written.
    assert _audit_count(db_path) == 1


# -------------------- Test 3: N concurrent toggles, audit-count == N -----


def test_concurrent_toggles_audit_count_matches(
    client: TestClient, db_path: Path,
) -> None:
    """Concurrent toggles → audit row count equals toggle count.

    Even when two toggles see the same ``old_value`` (the read in
    ``set_flag_runtime`` is not under the same lock as the write — the
    lock is taken twice), every toggle still writes its own audit row.
    The final flag value is implementation-defined ("last writer wins"
    under CPython GIL serialization), but the audit count must be exact.
    """
    n_toggles = 8  # below the 10/hour rate-limit ceiling
    barrier = threading.Barrier(n_toggles)
    statuses: list[int] = []
    status_lock = threading.Lock()

    def _toggle(i: int) -> None:
        barrier.wait(timeout=10.0)
        # Alternate enabled values to maximize audit-row variation.
        status = _toggle_via_api(
            client, enabled=bool(i % 2), reason=f"concurrent-{i}",
        )
        with status_lock:
            statuses.append(status)

    with ThreadPoolExecutor(max_workers=n_toggles) as pool:
        futs = [pool.submit(_toggle, i) for i in range(n_toggles)]
        for f in futs:
            f.result(timeout=10.0)

    # Every toggle returned 200 (no rate-limit hits within budget).
    assert statuses == [200] * n_toggles, statuses

    # Audit row count equals attempted toggle count — no drops.
    assert _audit_count(db_path) == n_toggles

    # Final flag state is whichever toggle physically wrote last; the
    # public API call returned a final value that matches the dict.
    final_state = ff.is_enabled(_FLAG)
    assert isinstance(final_state, bool)


# -------------------- Test 4: cache invalidation in same process --------


def test_cache_invalidation_on_toggle(
    client: TestClient, db_path: Path,
) -> None:
    """Toggle, then read in the same process → reader sees new value.

    The flag system has no TTL cache — the runtime-override dict IS the
    cache, and a write under ``_LOCK`` is immediately visible to the
    next read. Pin that invariant so a future "optimization" that adds
    a per-process TTL doesn't silently introduce stale reads.
    """
    assert ff.is_enabled(_FLAG) is False

    # Toggle ON.
    assert _toggle_via_api(client, enabled=True, reason="invalidate-on") == 200
    assert ff.is_enabled(_FLAG) is True, "stale read after toggle ON"

    # Toggle OFF in the same test process.
    assert _toggle_via_api(client, enabled=False, reason="invalidate-off") == 200
    assert ff.is_enabled(_FLAG) is False, "stale read after toggle OFF"

    # Two audit rows: one ON, one OFF.
    rows = _audit_rows(db_path)
    assert len(rows) == 2
    assert rows[0][:2] == ("false", "true")
    assert rows[1][:2] == ("true", "false")


# -------------------- Test 5: no TTL cache (cross-process semantics) --


def test_cache_invalidation_across_processes(
    client: TestClient, db_path: Path,
) -> None:
    """Pin the architectural invariant: there is NO in-process TTL cache.

    The S13 task spec asks: "if the cache is in-process per worker, …
    Verify a TTL exists and is short (≤30s) so flag toggles propagate.
    Pin the TTL constant." After auditing
    ``app.core.feature_flags`` we confirm there is **no time-based
    cache** in this codebase — the runtime override is a plain dict
    guarded by a lock, written synchronously by ``set_flag_runtime``
    and read synchronously by ``is_enabled``. There is therefore no
    TTL constant to pin; the invariant to pin instead is "no module
    exposes a TTL_SECONDS or similar cache-expiry hook." A future
    refactor that adds per-process caching MUST also publish a
    constant and update this test to pin it ≤30s.
    """
    # The module exposes no TTL / cache_seconds attribute today.
    forbidden = {"TTL", "TTL_SECONDS", "CACHE_TTL", "CACHE_TTL_SECONDS"}
    found = forbidden & set(vars(ff).keys())
    assert not found, (
        f"feature_flags module gained a TTL hook ({found!r}); update this "
        f"test to pin the value ≤ 30s and document the cross-process "
        f"propagation contract."
    )

    # And every read is observably live: a write is visible on the very
    # next call (no need to sleep, no eventual-consistency window).
    assert ff.is_enabled(_FLAG) is False
    assert _toggle_via_api(client, enabled=True, reason="no-ttl") == 200
    assert ff.is_enabled(_FLAG) is True  # immediate, not after a TTL


# -------------------- Test 6: 50-toggle burst, no lost audit rows ------


def test_no_lost_audit_under_burst(
    client: TestClient, db_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 50-toggle burst → exactly 50 audit rows. No silent drops.

    The route enforces a 10/hour per-actor rate limit. To exercise the
    audit-write path 50 times without artificial throttling we patch
    ``_check_rate_limit`` to always allow — this lets the SQLite
    audit-insert path take the full burst. Production callers stay
    behind the limit, but the persistence layer must still cope when
    the limiter is widened (e.g. multiple admin tokens) or replaced.
    """
    monkeypatch.setattr(
        "app.routes.admin_flags._check_rate_limit", lambda actor_hash: True,
    )

    n_toggles = 50
    barrier = threading.Barrier(n_toggles)

    def _toggle(i: int) -> int:
        barrier.wait(timeout=15.0)
        return _toggle_via_api(
            client, enabled=bool(i % 2), reason=f"burst-{i:02d}",
        )

    with ThreadPoolExecutor(max_workers=n_toggles) as pool:
        futs = [pool.submit(_toggle, i) for i in range(n_toggles)]
        statuses = [f.result(timeout=15.0) for f in futs]

    # All 50 succeed: rate-limit patched, audit table accepts every insert.
    failures = [s for s in statuses if s != 200]
    assert not failures, f"non-200 toggles under burst: {failures!r}"

    # No silent audit-row drops.
    assert _audit_count(db_path) == n_toggles

    # And the audit row contents are well-formed: every reason is one of
    # the burst-NN labels we emitted, exactly once.
    rows = _audit_rows(db_path)
    reasons = sorted(r[2] for r in rows)
    expected = sorted(f"burst-{i:02d}" for i in range(n_toggles))
    assert reasons == expected
