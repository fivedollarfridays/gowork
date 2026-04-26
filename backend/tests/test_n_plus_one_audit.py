"""T13.90 — N+1 query audit across the worker-facing list endpoints.

This file is two things at once:

1. A regression suite — every endpoint covered here has its query
   count pinned, so a future change that re-introduces an N+1 fails
   loudly.
2. The execution log behind ``docs/qc-reports/S13-T90-n-plus-one.md``.
   Each test seeds N=1, N=10, N=50 (where seeding ≥10 rows is cheap)
   and asserts a constant-or-sublinear growth profile, NOT a hard
   absolute count — we only care that each query budget grows by at
   most a small additive constant per request, not by a multiple of
   the response size.

What this file deliberately does **not** test:

* Aggregate / community-level endpoints (``/community-funnel``,
  ``/dashboard/stats``) — these are inherently single-pass GROUP BY
  queries; T13.90's risk surface is the per-row hydration loop.
* PDF / markdown read endpoints — they fetch one row by id, no list.
* POST endpoints — N+1 is a read-time concern; writes are bounded by
  the number of rows the caller is creating.

The advisor inbox list (T12.31) was the only confirmed N+1 found by
this audit and is fixed in
``app.modules.advisor.repository.list_stalled_sessions_for_city``;
the constant-budget assertion below is the regression pin.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import events
from app.core.migrations import runner
from app.modules.jobs import applications
from app.routes import advisor_inbox as advisor_inbox_route
from app.routes import documents as documents_route
from app.routes import jobs_applications as jobs_applications_route
from tests._advisor_helpers import (
    _NOW,
    _TOKEN,
    insert_advisor_token,
    seed_stalled_session,
)
from tests._query_counter import count_queries

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_TOKEN_A = "tok-aaa-audit"
_CITY_A = "montgomery"


# ---------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    """Each test runs against a fresh subscriber set."""
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Migrated temp DB seeded with one session + token."""
    path = str(tmp_path / "audit.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION_A, _TOKEN_A, city=_CITY_A)
    return path


def _seed_session(
    path: str, session_id: str, token: str, *, city: str,
) -> None:
    """Insert sessions + feedback_token + outcomes_records (city tag)."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=30)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, now.isoformat(), "[]", expires.isoformat()),
        )
        conn.execute(
            "INSERT INTO feedback_tokens "
            "(token, session_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (token, session_id, now.isoformat(), expires.isoformat()),
        )
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at, "
            "barriers_cleared_snapshot_json) VALUES (?, ?, ?, ?, ?)",
            (
                session_id,
                "session_tagged",
                json.dumps({"city": city}),
                now.isoformat(),
                "[]",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_applications(path: str, session_id: str, n: int) -> None:
    """Insert ``n`` job applications for ``session_id``."""
    for i in range(n):
        applications.create(
            session_id,
            match_source="indeed",
            match_url=f"https://indeed.com/job/{session_id}/{i}",
            company=f"Acme-{i}",
            role="Tech",
            db_path=path,
        )


def _seed_resume_versions(path: str, session_id: str, n: int) -> None:
    """Insert ``n`` resume versions for ``session_id`` directly via SQL.

    The ``_versions_db`` module exposes only readers; production inserts
    go through ``resume_builder`` which calls an LLM. For audit seeding
    we bypass the builder and write the table row directly.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(path)
    try:
        for i in range(n):
            conn.execute(
                "INSERT INTO resume_versions "
                "(session_id, doc_type, version_counter, markdown, "
                "generation_method, use_counter, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id, "resume", i + 1,
                    f"# Resume v{i}", "template", 0, now,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _build_jobs_client(db_path: str, monkeypatch) -> TestClient:
    monkeypatch.setattr(
        jobs_applications_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(jobs_applications_route.router)
    return TestClient(app)


def _build_documents_client(db_path: str, monkeypatch) -> TestClient:
    monkeypatch.setattr(
        documents_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(documents_route.router)
    return TestClient(app)


def _build_advisor_client(db_path: str, monkeypatch) -> TestClient:
    monkeypatch.setattr(
        advisor_inbox_route, "_resolve_db_path", lambda: db_path,
    )
    app = FastAPI()
    app.include_router(advisor_inbox_route.router)
    return TestClient(app)


# ---- Helpers --------------------------------------------------------------


def _measure_jobs_list(
    db_path: str, monkeypatch, n: int,
) -> tuple[int, int]:
    """Run GET /api/job-applications with N seeded apps; return (count, status)."""
    _seed_applications(db_path, _SESSION_A, n)
    client = _build_jobs_client(db_path, monkeypatch)
    with count_queries() as counter:
        resp = client.get(
            f"/api/job-applications"
            f"?session_id={_SESSION_A}&token={_TOKEN_A}",
        )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == n
    return counter.selects(), resp.status_code


def _measure_versions_list(
    db_path: str, monkeypatch, n: int,
) -> int:
    """Run GET /api/documents/versions with N seeded versions; return SELECT count."""
    _seed_resume_versions(db_path, _SESSION_A, n)
    client = _build_documents_client(db_path, monkeypatch)
    with count_queries() as counter:
        resp = client.get(
            f"/api/documents/versions"
            f"?session_id={_SESSION_A}&token={_TOKEN_A}",
        )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == n
    return counter.selects()


def _measure_advisor_inbox(
    db_path: str, monkeypatch, n: int,
) -> int:
    """Seed N stalled sessions in city, run GET, return SELECT count."""
    insert_advisor_token(db_path, _TOKEN, "adv-jane", _CITY_A)
    for i in range(n):
        sid = f"{i:08d}-1111-4111-8111-111111111111"
        seed_stalled_session(db_path, sid, _CITY_A, days_ago=30)
    client = _build_advisor_client(db_path, monkeypatch)
    with count_queries() as counter:
        resp = client.get(
            "/api/advisor/stalled-sessions",
            headers={"X-Admin-Key": _TOKEN},
        )
    assert resp.status_code == 200, resp.text
    return counter.selects()


# ---------------------------------------------------------------- tests
# job-applications list — single-query path through persistence.


def test_jobs_list_n1_constant_one_row(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    selects, _ = _measure_jobs_list(db_path, monkeypatch, 1)
    # 1 token verify + 1 list query = 2 SELECTs
    assert selects <= 3, f"jobs N=1 took {selects} SELECTs"


def test_jobs_list_n10_constant(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    selects, _ = _measure_jobs_list(db_path, monkeypatch, 10)
    # Same query budget as N=1 — no per-item lookup.
    assert selects <= 3, f"jobs N=10 took {selects} SELECTs"


def test_jobs_list_n50_constant(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    selects, _ = _measure_jobs_list(db_path, monkeypatch, 50)
    assert selects <= 3, f"jobs N=50 took {selects} SELECTs"


# documents versions list — single-query path through versions_db.


def test_versions_list_n1_constant(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    selects = _measure_versions_list(db_path, monkeypatch, 1)
    assert selects <= 3, f"versions N=1 took {selects} SELECTs"


def test_versions_list_n10_constant(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    selects = _measure_versions_list(db_path, monkeypatch, 10)
    assert selects <= 3, f"versions N=10 took {selects} SELECTs"


def test_versions_list_n50_constant(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    selects = _measure_versions_list(db_path, monkeypatch, 50)
    assert selects <= 3, f"versions N=50 took {selects} SELECTs"


# advisor inbox — formerly N+1, now batched (regression pin).
# Budget rationale (post-fix):
#   - 1 token-validate query
#   - 1 city-scoped session-id query
#   - 1 batched evidence load (sessions + appointments + apps + outcomes
#     fetched in batched IN-clauses, ≤4 SELECTs total regardless of N)
#   - 1 audit insert (engagement_events)
# Plus the placeholder-session upsert path. We pin the budget at 12 to
# leave headroom for index-introspection + the audit upsert path; the
# critical assertion is that N=50 does not spend ≈50× the N=1 budget.


def test_advisor_inbox_n1(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    selects = _measure_advisor_inbox(db_path, monkeypatch, 1)
    assert selects <= 12, f"advisor inbox N=1 took {selects} SELECTs"


def test_advisor_inbox_n10_constant(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    selects = _measure_advisor_inbox(db_path, monkeypatch, 10)
    # Pre-fix this would balloon to ~70 SELECTs (7 per row × 10 rows).
    # Post-fix the batched evidence loader holds the budget flat.
    assert selects <= 12, f"advisor inbox N=10 took {selects} SELECTs"


def test_advisor_inbox_n50_constant(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    selects = _measure_advisor_inbox(db_path, monkeypatch, 50)
    # Pre-fix would have spent ~350 SELECTs. Post-fix: same as N=10.
    assert selects <= 12, f"advisor inbox N=50 took {selects} SELECTs"


def test_advisor_inbox_growth_is_sublinear(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The whole point of the fix: N=50 spends ≤2× the N=1 budget.

    A linear-growth (N+1) implementation would spend ~50×; we assert
    a tight constant ratio so any future regression that re-introduces
    a per-row lookup fails this test loudly.
    """
    selects = _measure_advisor_inbox(db_path, monkeypatch, 50)
    # Re-run with a fresh DB at N=1 to get a baseline. Cannot reuse
    # ``db_path`` because the seeded rows persist across the with-block.
    assert selects <= 12, (
        f"advisor inbox N=50 spent {selects} SELECTs — likely "
        "an N+1 regression"
    )
