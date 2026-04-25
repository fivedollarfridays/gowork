"""Demo-seed every-feature coverage guard (S13 T13.67).

Generalises and strengthens the T13.2 ``module_status_keys_have_at_least_one_
nonunknown_session`` invariant. Four behaviours are locked in here:

1. **Status-collector module coverage** — every module wired into
   :data:`app.modules.status_collector._MODULES` reports a non-``unknown``
   ``nightly_status`` for at least one demo session after the seed runs.
2. **Session-scoped table seed depth** — every session-scoped table that
   the seed promises to populate carries ≥1 row for at least one demo
   session id after seed. Tables intentionally not seeded are listed in
   :data:`UNSEEDED_TABLE_ALLOWLIST` with a one-line rationale so the
   "no demo state" decision is explicit.
3. **Production-module directory inventory** — walking
   ``backend/app/modules/`` produces a canonical list of module
   subdirectories. The list is pinned in :data:`PRODUCTION_MODULES` so
   adding a new module without updating the inventory fails the test.
4. **Production-module seed coverage** — every entry in
   :data:`PRODUCTION_MODULES` either appears in the seed (touches a
   table or feature the seed populates) OR is on the
   :data:`INFRASTRUCTURE_MODULES` allowlist with a documented reason
   (e.g. ``common``, ``data`` — pure type modules with no demo state).

Together, behaviours 3 and 4 form the drift guard: a new
``backend/app/modules/<new_module>/`` directory will fail the test
unless it is either seeded or explicitly excluded with a reason.

Why duplicate part of T13.2's assertion?
----------------------------------------
T13.2 already checks status-collector coverage. T13.67 keeps that
assertion (defence-in-depth) but locks the broader inventory + seed
depth in the same file so a future PR cannot silently add a module
without seed coverage by tweaking only one of the two layers.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from app.demo_seed import seed_worker_companion_sessions
from app.modules import status_collector


# --------------------------------------------------------------- constants


# Pinned list of production-module directories under ``backend/app/modules``.
# Every entry is a directory containing an ``__init__.py``. Adding a new
# module requires updating this list — that's the drift guard.
#
# Each entry lists the canonical module name as it appears on disk; the
# value is a one-line description so reviewers can sanity-check intent.
PRODUCTION_MODULES: dict[str, str] = {
    "advisor": "advisor inbox + token gate (T12.31)",
    "appointments": "career-center scheduler + email dispatch",
    "benefits": "Texas benefits eligibility + cliff calculator",
    "common": "shared temporal/health type models",
    "compliance": "export, retention, full_delete + audit trail",
    "credit": "credit-barrier types (legacy stub)",
    "criminal": "fair-chance employer index + expungement screen",
    "data": "shared data-layer types",
    "documents": "resume + cover-letter builders + injection filter",
    "engagement": "digest composer, reminder engine, stall classifier",
    "feedback": "visit / health / resource feedback tokens",
    "jobs": "applications module + community funnel analytics",
    "matching": "barrier-card affinity + commute estimator",
    "outcomes": "outcomes tracker + community insights aggregator",
    "pathway": "barrier-pathway engine + cliff navigator",
    "plan": "weekly review + action plan + daily progress",
    "resources": "findhelp + eligibility resource module",
}


# Modules that are **not** required to have demo seed state. Each entry
# explains *why* — usually because the module is pure types, no DB
# tables, or its DB tables are session-agnostic shared lookup data.
INFRASTRUCTURE_MODULES: dict[str, str] = {
    "common": (
        "type models only (ModuleStatus, StallLevel) — no DB tables, "
        "exercised transitively by every status_collector call"
    ),
    "data": (
        "shared data-layer types — no session-scoped state; tables it "
        "touches (e.g. resources lookup) are shared across all demo sessions"
    ),
    "credit": (
        "credit-barrier types only — credit barrier surfaces through "
        "barrier_relationships seed at the m001 level, not via a "
        "credit-specific demo row"
    ),
    "matching": (
        "pure compute over barrier_resources + transit_stops — no "
        "session-scoped tables; exercised by demo session profile data"
    ),
    "pathway": (
        "pathway engine reads sessions.profile + outcomes_records; both "
        "are seeded by the worker-companion seed transitively"
    ),
    "benefits": (
        "benefits eligibility runs against sessions.benefits_profile "
        "(seeded in app.demo_seed) — not a session-scoped table"
    ),
    "feedback": (
        "feedback tokens table IS populated by the QC seed spoke; the "
        "module itself is allowlisted because its production code path "
        "(token submission) is not part of the nightly seed flow"
    ),
    "resources": (
        "resources is a shared lookup table populated by m001 fixtures, "
        "not session-scoped. Demo sessions reference resources by id."
    ),
    "advisor": (
        "advisor_tokens IS seeded by the QC spoke; the advisor inbox "
        "demo state ships through outcomes_records city tagging, not "
        "an advisor-specific session table"
    ),
}


# Session-scoped tables (carrying ``session_id`` or FK -> sessions(id))
# that the worker-companion seed deliberately does NOT populate. Each
# entry must explain why so a future schema change forces a real
# decision (seed it OR add to this allowlist with a fresh reason).
UNSEEDED_TABLE_ALLOWLIST: dict[str, str] = {
    "plan_history": (
        "plan archive snapshots — produced only when a worker actually "
        "rewrites their plan; demo sessions ship pre-built plans"
    ),
    "record_profiles": (
        "criminal-record profile — populated only when worker runs the "
        "fair-chance assessment; demo seed does not exercise that flow"
    ),
    "resource_feedback": (
        "resource thumbs-up/down — produced only when worker submits "
        "feedback on a specific resource via the public token form"
    ),
    "share_tokens": (
        "plan share-link tokens — produced only when worker generates "
        "a public share URL; demo seed does not exercise that flow"
    ),
    "visit_feedback": (
        "career-center visit feedback — produced only when worker "
        "submits the post-visit survey; the legacy app.demo_seed "
        "(non-worker-companion) populates this for the older dataset"
    ),
    "worker_unavailability": (
        "worker availability windows — populated only when the worker "
        "explicitly blocks time on the scheduler; demo seed reuses "
        "the default open availability"
    ),
}


CITIES = ("montgomery", "fort-worth")
SESSIONS_PER_CITY = 5
EXPECTED_DEMO_SESSIONS = SESSIONS_PER_CITY * len(CITIES)


_MODULES_DIR = Path(__file__).resolve().parent.parent / "app" / "modules"


# Status-collector module name -> directory under ``backend/app/modules``.
# Centralised so Tests 4 + 5 share the same mapping; new status_collector
# entries must be reflected here.
_STATUS_COLLECTOR_DIRS: dict[str, str] = {
    "resume_builder": "documents",
    "cover_letter_builder": "documents",
    "applications": "jobs",
    "reminder_engine": "engagement",
}


# Modules whose feature is exercised by the seed but whose
# ``nightly_status`` is not wired into status_collector. Used by Test 4.
_SEEDED_BY_FEATURE: dict[str, str] = {
    "appointments": "insert_appointment plants one row per session",
    "compliance": "seed_compliance_audit + seed_feedback_tokens",
    "documents": (
        "insert_resume_version plants resume + cover_letter rows"
    ),
    "engagement": (
        "seed_engagement_window + seed_reminder_state + sendgrid opens"
    ),
    "jobs": "insert_application plants job_applications row",
    "outcomes": "insert_outcomes_rows plants city-tagged events",
    "plan": "insert_snapshot plants daily_progress_snapshots row",
    "criminal": (
        "criminal_record barrier surfaces through STATE_BARRIER + outcomes"
    ),
}


# --------------------------------------------------------------- helpers


def _migrated_db(tmp_path: Path, name: str = "coverage.db") -> str:
    """Return a freshly migrated DB path (all migrations applied)."""
    db_path = str(tmp_path / name)
    runner.apply_pending(db_path)
    return db_path


def _user_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' "
        "  AND name NOT LIKE 'sqlite_%' "
        "  AND name != 'schema_migrations' "
        "ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def _session_scoped_tables(conn: sqlite3.Connection) -> list[str]:
    """Tables with a ``session_id`` column or FK -> sessions(id)."""
    found: set[str] = set()
    for table in _user_tables(conn):
        cols = [
            c[1] for c in conn.execute(
                f"PRAGMA table_info({table})",
            ).fetchall()
        ]
        if "session_id" in cols:
            found.add(table)
            continue
        for fk in conn.execute(
            f"PRAGMA foreign_key_list({table})",
        ).fetchall():
            if fk[2] == "sessions" and fk[4] == "id":
                found.add(table)
                break
    return sorted(found)


def _module_directories() -> list[str]:
    """Return ``backend/app/modules/<name>/`` dirs that have ``__init__.py``."""
    if not _MODULES_DIR.exists():
        return []
    found: list[str] = []
    for child in sorted(_MODULES_DIR.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        if (child / "__init__.py").exists():
            found.append(child.name)
    return found


def _classify_table_seed_state(
    conn: sqlite3.Connection, scoped: list[str], session_ids: list[str],
) -> tuple[set[str], set[str]]:
    """Return (seeded, unseeded) sets for the given session-scoped tables.

    A table is "seeded" when it has ≥1 row whose ``session_id`` matches
    one of ``session_ids``.
    """
    seeded: set[str] = set()
    unseeded: set[str] = set()
    placeholder = ",".join(["?"] * len(session_ids))
    for table in scoped:
        row = conn.execute(
            f"SELECT 1 FROM {table} "
            f"WHERE session_id IN ({placeholder}) LIMIT 1",
            session_ids,
        ).fetchone()
        if row is not None:
            seeded.add(table)
        else:
            unseeded.add(table)
    return seeded, unseeded


def _module_seed_classification(module_name: str) -> str | None:
    """Return one of {'feature', 'status', 'infrastructure'} or None.

    Used by Test 4 to compute coverage in a single pass without a long
    branching block in the test body itself.
    """
    if module_name in _SEEDED_BY_FEATURE:
        return "feature"
    seeded_via_status = {
        _STATUS_COLLECTOR_DIRS[name] for name, _ in status_collector._MODULES
    }
    if module_name in seeded_via_status:
        return "status"
    if module_name in INFRASTRUCTURE_MODULES:
        return "infrastructure"
    return None


# --------------------------------------------------------------- fixtures


@pytest.fixture
def seeded_db(tmp_path: Path) -> str:
    """Migrated DB with the worker-companion demo seed applied."""
    db_path = _migrated_db(tmp_path)
    pinned = datetime(2026, 4, 24, 12, 0, tzinfo=timezone.utc)
    seed_worker_companion_sessions(db_path=db_path, now=pinned)
    return db_path


# --------------------------------------------------------------- Test 1


def test_status_collector_modules_have_demo_coverage(seeded_db: str) -> None:
    """Every status_collector module reports non-``unknown`` for ≥1 session.

    Hard-coded expectation: the four modules wired into ``_MODULES``
    today (resume_builder, cover_letter_builder, applications,
    reminder_engine) must each light up green for at least one of the
    10 demo sessions. A regression in any single module's seed coverage
    surfaces here with the offending module name.
    """
    conn = sqlite3.connect(seeded_db)
    try:
        ids = [
            r[0] for r in conn.execute("SELECT id FROM sessions").fetchall()
        ]
    finally:
        conn.close()

    assert len(ids) == EXPECTED_DEMO_SESSIONS, (
        f"expected {EXPECTED_DEMO_SESSIONS} demo sessions; got {len(ids)}"
    )

    healths_per_module: dict[str, set[str]] = {}
    for sid in ids:
        for status in status_collector.collect_all(sid, db_path=seeded_db):
            healths_per_module.setdefault(status.module_name, set()).add(
                status.health,
            )

    expected_module_names = {name for name, _ in status_collector._MODULES}
    seen = set(healths_per_module)
    assert seen == expected_module_names, (
        f"status_collector returned modules {seen!r}; "
        f"expected {expected_module_names!r}"
    )

    only_unknown = [
        module_name for module_name, healths in healths_per_module.items()
        if healths == {"unknown"}
    ]
    assert not only_unknown, (
        "status_collector modules with no non-unknown demo coverage: "
        f"{only_unknown}; full health map: {healths_per_module}"
    )


# --------------------------------------------------------------- Test 2


def test_session_scoped_tables_seeded(seeded_db: str) -> None:
    """Every session-scoped table is either seeded or on the unseeded allowlist.

    Reuses the introspection contract from T13.70: the ``session_id``-
    bearing tables form the canonical inventory. After the seed runs,
    every such table must either:

    * have ≥1 row for one of the demo session ids, OR
    * appear in :data:`UNSEEDED_TABLE_ALLOWLIST` with a documented reason.

    Any other table fails this test loudly so a new session-scoped
    migration cannot silently land without a seed update or an
    explicit "no demo state" decision.
    """
    conn = sqlite3.connect(seeded_db)
    try:
        scoped = _session_scoped_tables(conn)
        ids = [
            r[0] for r in conn.execute("SELECT id FROM sessions").fetchall()
        ]
        seeded, unseeded = _classify_table_seed_state(conn, scoped, ids)
    finally:
        conn.close()

    overlap = seeded & set(UNSEEDED_TABLE_ALLOWLIST)
    assert not overlap, (
        f"tables seeded AND on UNSEEDED_TABLE_ALLOWLIST: {sorted(overlap)} "
        "— remove them from the allowlist"
    )

    undocumented = unseeded - set(UNSEEDED_TABLE_ALLOWLIST)
    assert not undocumented, (
        f"session-scoped tables with no seed coverage and no allowlist "
        f"entry: {sorted(undocumented)}. Either extend "
        "app.demo_seed_s12b to populate them or add an entry to "
        "UNSEEDED_TABLE_ALLOWLIST with a one-line reason."
    )


# --------------------------------------------------------------- Test 3


def test_canonical_module_directories_documented() -> None:
    """Every ``backend/app/modules/<dir>/`` is in ``PRODUCTION_MODULES``.

    Drift guard. Adding a new module directory without an entry in
    :data:`PRODUCTION_MODULES` fails this test with the offending name,
    forcing the dev to declare intent (does the module need seed state?).
    """
    on_disk = set(_module_directories())
    documented = set(PRODUCTION_MODULES)

    extra_on_disk = on_disk - documented
    assert not extra_on_disk, (
        "Found new module directories not documented in PRODUCTION_MODULES: "
        f"{sorted(extra_on_disk)}. Add an entry to PRODUCTION_MODULES "
        "describing the module, then either ensure the demo seed "
        "exercises it OR add the module to INFRASTRUCTURE_MODULES with "
        "a documented reason."
    )

    extra_documented = documented - on_disk
    assert not extra_documented, (
        "PRODUCTION_MODULES references modules that no longer exist on "
        f"disk: {sorted(extra_documented)}. Remove stale entries."
    )


# --------------------------------------------------------------- Test 4


def test_every_production_module_seeded_or_excluded() -> None:
    """Every PRODUCTION_MODULES entry is seeded OR on the infra allowlist.

    A module is considered "seeded" when one of these is true:

    * it appears in :data:`status_collector._MODULES` (status-coverage
      verified by Test 1), OR
    * it lives in :data:`_SEEDED_BY_FEATURE` — modules whose production
      tables receive seed rows but whose ``nightly_status`` is not
      wired into the collector.

    Otherwise the module must be on :data:`INFRASTRUCTURE_MODULES` with
    a documented "no seed needed" reason. Any other case is a coverage
    gap.
    """
    uncovered = [
        module_name for module_name in PRODUCTION_MODULES
        if _module_seed_classification(module_name) is None
    ]
    assert not uncovered, (
        "Production modules with no demo seed coverage and no "
        f"infrastructure-allowlist entry: {sorted(uncovered)}. Either "
        "extend the demo seed to exercise the module, or add it to "
        "INFRASTRUCTURE_MODULES with a documented reason."
    )


def test_inventory_documentation_quality() -> None:
    """Defensive: every pinned-inventory entry carries a real description.

    Cheap guard against a future PR that adds an entry but leaves the
    description blank or trivially short — keeps the inventories
    self-documenting.
    """
    for module_name, reason in INFRASTRUCTURE_MODULES.items():
        assert reason and len(reason) > 20, (
            f"INFRASTRUCTURE_MODULES[{module_name!r}] missing a "
            "meaningful (>20 char) reason"
        )

    for module_name, desc in PRODUCTION_MODULES.items():
        assert desc and len(desc) > 5, (
            f"PRODUCTION_MODULES[{module_name!r}] missing a description"
        )

    for table, reason in UNSEEDED_TABLE_ALLOWLIST.items():
        assert reason and len(reason) > 20, (
            f"UNSEEDED_TABLE_ALLOWLIST[{table!r}] missing a "
            "meaningful (>20 char) reason"
        )


# --------------------------------------------------------------- Test 5: cross-check


def test_status_collector_modules_belong_to_documented_dirs() -> None:
    """Every status_collector module's directory is in PRODUCTION_MODULES.

    Cross-check between the two pinned inventories: a module in the
    nightly status collector whose backing directory is not in
    PRODUCTION_MODULES means the inventory has drifted.
    """
    for module_name, _ in status_collector._MODULES:
        assert module_name in _STATUS_COLLECTOR_DIRS, (
            f"status_collector module {module_name!r} is not mapped to "
            "a directory in this test — update "
            "_STATUS_COLLECTOR_DIRS in test_demo_seed_coverage.py"
        )
        backing_dir = _STATUS_COLLECTOR_DIRS[module_name]
        assert backing_dir in PRODUCTION_MODULES, (
            f"status_collector module {module_name!r} maps to "
            f"directory {backing_dir!r} which is not in PRODUCTION_MODULES"
        )
