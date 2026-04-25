"""Aggregator-level tests for ``status_collector.collect_all`` (T13.69).

T12.25b introduced four per-module ``nightly_status`` callables and a
single aggregator (:mod:`app.modules.status_collector`) that fans them
out and returns a homogeneous ``list[ModuleStatus]``. T13.107
(cross-module integrity, later) will lock in the aggregator's wire
shape; this file pins the *current* shape and the partial / total
failure policy so a future change has to come through here.

Coverage at a glance
--------------------
* ``test_all_green_shape`` — call ``collect_all`` against a freshly
  seeded DB (T13.2 demo seed) and assert every documented module key
  appears with the documented per-module shape.
* ``test_partial_failure_distinct`` — monkeypatch one module's
  ``nightly_status`` to raise; aggregator surfaces it as a sentinel
  (``health='unknown'``, ``signals['error']``) without dropping it.
* ``test_total_failure_aggregator_error`` — monkeypatch ALL four
  modules to raise; aggregator returns four sentinels and does NOT
  itself raise (current policy: never propagate).
* ``test_per_module_isolation`` — failure in module A does not leak
  into module B's status (independent try/except per module).
* ``test_status_keys_documented_in_module_status_contracts`` —
  drift-detection guard: the set of module names returned by
  ``collect_all`` must equal the registered ``_MODULES`` tuple.
* ``test_aggregator_used_in_DigestResult`` — the orchestrator's
  compose step (``compose_digest``) plumbs ``collect_all`` output
  straight onto ``DigestResult.module_status``.

Mirrors the test style of ``test_module_status.py`` (the per-module
contract suite) and uses the production migration runner + the T13.2
``seed_worker_companion_sessions`` so the assertions live against the
same wiring used by ops.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.core import feature_flags
from app.core.migrations import runner
from app.demo_seed import seed_worker_companion_sessions
from app.modules.common.temporal_types import ModuleStatus
from app.modules.documents import cover_letter_builder, resume_builder
from app.modules.engagement import digest_composer, reminder_engine
from app.modules.jobs import applications
from app.modules.status_collector import _MODULES, collect_all

# ----- Test constants -------------------------------------------------

# A frozen "now" inside the demo seed's freshness windows; the seed
# stamps progress events at 1d / 4d / 10d / 18d / 20d ages off this
# anchor, so picking a date here is what the per-module nightly_status
# helpers use to classify health.
_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
_FOR_DATE = date(2026, 4, 23)

# The four module names the collector currently registers, in registration
# order. Pinned here so an accidental rename in ``_MODULES`` triggers a
# loud test failure rather than silent shape drift.
_EXPECTED_MODULE_NAMES: frozenset[str] = frozenset(
    {
        "resume_builder",
        "cover_letter_builder",
        "applications",
        "reminder_engine",
    }
)


# ----- Fixtures -------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_feature_flags() -> None:
    """Keep feature-flag state isolated between tests."""
    feature_flags._reset_state_for_tests()
    yield
    feature_flags._reset_state_for_tests()


@pytest.fixture
def seeded_db(tmp_path: Path) -> str:
    """Return a temp DB path with all migrations applied + demo seed.

    Uses the production migration runner + the T13.2 worker-companion
    demo seed so each registered module has at least *some* data to
    report on. Several seeded sessions exist (5 stall states × 2
    cities); we pick one stable session id to drive the per-module
    calls — the exact choice doesn't matter because all-green only
    asserts shape, not health values.
    """
    db_path = str(tmp_path / "aggregator.db")
    runner.apply_pending(db_path)
    seed_worker_companion_sessions(db_path=db_path, now=_NOW)
    return db_path


@pytest.fixture
def seeded_session(seeded_db: str) -> str:
    """Return one demo session id from the seeded DB."""
    conn = sqlite3.connect(seeded_db)
    try:
        row = conn.execute(
            "SELECT id FROM sessions WHERE demo = 1 ORDER BY id LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, "demo seed produced no sessions"
    return str(row[0])


# ----- Cycle 1: all-green shape ---------------------------------------


def test_all_green_shape(seeded_db: str, seeded_session: str) -> None:
    """All four modules return a homogeneous ``ModuleStatus`` list.

    The seeded DB carries enough rows that every module has *something*
    to report (a non-``unknown`` state is not strictly required — what
    matters is the wire shape: same module names, all ``ModuleStatus``
    instances, same set of fields).
    """
    results = collect_all(seeded_session, db_path=seeded_db, now=_NOW)

    # Cardinality + ordering: deterministic, matches _MODULES.
    assert len(results) == len(_MODULES)
    returned_names = [r.module_name for r in results]
    expected_order = [name for name, _ in _MODULES]
    assert returned_names == expected_order

    # Set equality drift guard: any add/rename in _MODULES must update
    # _EXPECTED_MODULE_NAMES.
    assert set(returned_names) == _EXPECTED_MODULE_NAMES

    # Per-module shape: each entry is a ``ModuleStatus`` with the four
    # documented fields.
    for status in results:
        assert isinstance(status, ModuleStatus)
        assert status.module_name in _EXPECTED_MODULE_NAMES
        assert status.health in {"healthy", "degraded", "unknown"}
        assert isinstance(status.signals, dict)
        # last_activity_at may be None for unknown but must be a
        # tz-aware datetime when present.
        if status.last_activity_at is not None:
            assert status.last_activity_at.tzinfo is not None


def test_all_green_shape_keys_match_module_status_model(
    seeded_db: str, seeded_session: str,
) -> None:
    """Every entry exposes the canonical ``ModuleStatus`` field set."""
    results = collect_all(seeded_session, db_path=seeded_db, now=_NOW)
    canonical_fields = {
        "module_name", "health", "signals", "last_activity_at",
    }
    for status in results:
        dumped = status.model_dump()
        assert set(dumped.keys()) == canonical_fields


# ----- Cycle 2: partial failure surfaced distinctly -------------------


def test_partial_failure_distinct(
    seeded_db: str,
    seeded_session: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One failing module surfaces as ``unknown`` + ``error`` signal.

    The other three continue to report normally. The failing module is
    NOT silently dropped — its slot is preserved so downstream consumers
    can spot the gap.
    """
    def _boom(*_a, **_kw) -> None:
        raise RuntimeError("simulated cover-letter explosion")

    monkeypatch.setattr(cover_letter_builder, "nightly_status", _boom)

    results = collect_all(seeded_session, db_path=seeded_db, now=_NOW)

    # Slot preserved.
    assert len(results) == len(_MODULES)
    by_name = {r.module_name: r for r in results}
    assert set(by_name.keys()) == _EXPECTED_MODULE_NAMES

    # The failing module is sentinel-shaped.
    failed = by_name["cover_letter_builder"]
    assert failed.health == "unknown"
    assert "error" in failed.signals
    assert "simulated cover-letter explosion" in failed.signals["error"]
    assert failed.last_activity_at is None

    # The other three still report a real (non-error) signals dict.
    for name in _EXPECTED_MODULE_NAMES - {"cover_letter_builder"}:
        other = by_name[name]
        assert "error" not in other.signals, (
            f"{name} should not be tainted by cover_letter_builder failure"
        )


# ----- Cycle 3: total failure → all-failed (no aggregator-level raise) -


def test_total_failure_aggregator_error(
    seeded_db: str,
    seeded_session: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every module raises → aggregator returns four sentinels, no raise.

    Documented policy (status_collector.py): the aggregator NEVER
    propagates a per-module exception; total failure means every slot
    is a ``health='unknown'`` sentinel with an ``error`` signal.
    """
    def _boom(*_a, **_kw) -> None:
        raise RuntimeError("total module collapse")

    monkeypatch.setattr(resume_builder, "nightly_status", _boom)
    monkeypatch.setattr(cover_letter_builder, "nightly_status", _boom)
    monkeypatch.setattr(applications, "nightly_status", _boom)
    monkeypatch.setattr(reminder_engine, "nightly_status", _boom)

    # Must not raise.
    results = collect_all(seeded_session, db_path=seeded_db, now=_NOW)

    assert len(results) == len(_MODULES)
    for status in results:
        assert status.health == "unknown"
        assert status.signals.get("error") == "total module collapse"
        assert status.last_activity_at is None
    assert {r.module_name for r in results} == _EXPECTED_MODULE_NAMES


# ----- Cycle 4: per-module isolation ----------------------------------


def test_per_module_isolation(
    seeded_db: str,
    seeded_session: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Module A's exception does not leak into module B.

    Each module is wrapped in its own try/except inside the collector;
    one bad implementation cannot poison a sibling's signals.
    """
    class _DistinctError(Exception):
        pass

    def _module_a_boom(*_a, **_kw) -> None:
        raise _DistinctError("isolation marker A")

    monkeypatch.setattr(applications, "nightly_status", _module_a_boom)

    results = collect_all(seeded_session, db_path=seeded_db, now=_NOW)
    by_name = {r.module_name: r for r in results}

    # Failing module reports its specific marker.
    a = by_name["applications"]
    assert a.health == "unknown"
    assert a.signals.get("error") == "isolation marker A"

    # The three siblings have NO leakage of the marker.
    for name in _EXPECTED_MODULE_NAMES - {"applications"}:
        sibling = by_name[name]
        sibling_error = sibling.signals.get("error")
        assert sibling_error != "isolation marker A"
        # Sibling should also not carry an unrelated 'error' key (it
        # ran successfully on the seeded DB).
        assert "error" not in sibling.signals, (
            f"{name} signals: {sibling.signals!r}"
        )


# ----- Cycle 5: registered-modules drift guard ------------------------


def test_status_keys_documented_in_module_status_contracts(
    seeded_db: str, seeded_session: str,
) -> None:
    """Every name returned by ``collect_all`` is in ``_MODULES``.

    This is the future-proofing check: when someone adds a 5th module,
    they MUST update ``_MODULES`` (the registration source of truth)
    and they SHOULD update ``_EXPECTED_MODULE_NAMES`` here. The first
    catches a runtime drop; the second catches a registration gap.
    """
    registered = {name for name, _ in _MODULES}
    assert registered == _EXPECTED_MODULE_NAMES, (
        "_MODULES has drifted from the test expectation; update both."
    )

    results = collect_all(seeded_session, db_path=seeded_db, now=_NOW)
    returned = {r.module_name for r in results}

    # No silent drop: every registered module appears in the result.
    assert returned == registered

    # No phantom additions: nothing came back that wasn't registered.
    assert returned <= registered


def test_status_collector_module_count_matches_registered() -> None:
    """``_MODULES`` cardinality matches the documented module count.

    Pinned at 4 (T12.25b's original four). Bumping this is intentional
    and forces a code review of the aggregator contract.
    """
    assert len(_MODULES) == 4


# ----- Cycle 6: DigestResult uses aggregator output -------------------


def test_aggregator_used_in_DigestResult(
    seeded_db: str, seeded_session: str,
) -> None:
    """``DigestResult.module_status`` is the aggregator's output.

    Calls the orchestrator's compose step and asserts the
    ``module_status`` field carries exactly the four ``ModuleStatus``
    entries the aggregator produced — same names, same field shape.
    Future-proofs the seam between the digest composer and T12.31's
    advisor inbox.
    """
    digest = digest_composer.compose_digest(
        seeded_session, _FOR_DATE,
        db_path=seeded_db, city="montgomery", now=_NOW,
    )

    assert hasattr(digest, "module_status")
    assert isinstance(digest.module_status, list)
    assert len(digest.module_status) == len(_MODULES)

    names_on_digest = {s.module_name for s in digest.module_status}
    assert names_on_digest == _EXPECTED_MODULE_NAMES

    # Every entry on the digest is a ModuleStatus (not a dict / proxy).
    for entry in digest.module_status:
        assert isinstance(entry, ModuleStatus)


def test_aggregator_failure_visible_through_DigestResult(
    seeded_db: str,
    seeded_session: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A module failure surfaces on the digest, not as a composer crash.

    Confirms the seam holds end-to-end: a per-module exception turns
    into a sentinel inside ``DigestResult.module_status`` rather than
    aborting the digest pipeline.
    """
    def _boom(*_a, **_kw) -> None:
        raise RuntimeError("digest-seam failure marker")

    monkeypatch.setattr(reminder_engine, "nightly_status", _boom)

    digest = digest_composer.compose_digest(
        seeded_session, _FOR_DATE,
        db_path=seeded_db, city="montgomery", now=_NOW,
    )

    by_name = {s.module_name: s for s in digest.module_status}
    failed = by_name["reminder_engine"]
    assert failed.health == "unknown"
    assert failed.signals.get("error") == "digest-seam failure marker"
