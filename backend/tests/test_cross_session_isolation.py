"""Cross-session isolation regression for every session-owned endpoint (T13.63).

The contract under test
=======================

Every endpoint that accepts a ``session_id`` together with a session-bound
``token`` (or ``session_token``) must reject a request that pairs
session-A's id with session-B's token. The required response status is
**403** — meaning "your token is valid, but it does not own this
session". Anything else is a finding:

* **200 / 201 / 204** — the endpoint mutated or read sess-A data using
  sess-B's token. Unambiguous IDOR; the test must fail loudly with the
  endpoint name.
* **401** — the endpoint did not check ownership at all (it treated the
  cross-session token as invalid). That is also a fail; the right
  response is 403, because the token IS valid, just for the wrong
  session. A 401 hides the IDOR risk in benign-looking auth language.
* **404** — the endpoint requires extra setup (existing resource owned
  by the target session) that the bare scaffold does not provide. The
  endpoint is allowlisted with a documented reason.

Endpoint discovery
==================

Routes are enumerated from the live ``app.routes`` (FastAPI introspection
in :mod:`tests._route_inventory`). The heuristic flags any route whose
endpoint signature *or* declared body model includes both a ``session_id``
parameter and a ``token`` / ``session_token`` parameter. A new endpoint
that lacks ownership enforcement will show up here automatically and
fail the cross-session assertion until either:

1. The route is fixed to call ``require_session_token`` /
   ``verify_token`` *before* doing any work, or
2. It is added to ``PUBLIC_ENDPOINTS`` (in
   :mod:`tests._cross_session_fixtures`) with a justification.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.migrations import runner
from tests._cross_session_fixtures import (
    PUBLIC_ENDPOINTS,
    REQUIRED_FIELD_PLACEHOLDERS,
)
from tests._fake_clock import freeze_time
from tests._route_inventory import (
    RouteSpec,
    all_route_specs,
    discover_session_routes,
)


# --------------------------------------------------------------- fixtures


# UUID-shaped ids: several routes (plan, simulate, pathway, insights,
# barrier-intel chat, feedback) declare ``session_id`` with a strict
# UUID regex so a non-UUID input never reaches the ownership check.
# Using real UUIDs lets the test exercise the actual auth path.
_SESS_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_SESS_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_TOK_A = "tok-cross-a-aaaaaaaaaaaaaaaaaaaaaaaa"
_TOK_B = "tok-cross-b-bbbbbbbbbbbbbbbbbbbbbbbb"
_FROZEN_INSTANT = "2026-04-22T12:00:00+00:00"


@pytest.fixture
def two_session_db(tmp_path: Path) -> str:
    """Migrated SQLite DB seeded with two sessions + two feedback tokens."""
    db_path = str(tmp_path / "cross_session.db")
    runner.apply_pending(db_path)
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        for sid in (_SESS_A, _SESS_B):
            conn.execute(
                "INSERT INTO sessions (id, created_at, barriers, profile, "
                "expires_at) VALUES (?, ?, ?, ?, ?)",
                (sid, now.isoformat(), "[]", "{}", expires),
            )
        for tok, sid in ((_TOK_A, _SESS_A), (_TOK_B, _SESS_B)):
            conn.execute(
                "INSERT INTO feedback_tokens "
                "(token, session_id, created_at, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (tok, sid, now.isoformat(), expires),
            )
        conn.commit()
    finally:
        conn.close()
    return db_path


@pytest.fixture
def isolation_client(
    two_session_db: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """TestClient wired to the two-session DB for both sync + async routes.

    Sync routers (appointments / documents / jobs_applications / engagement
    / compliance / etc.) consult ``_appointments_helpers.resolve_db_path``;
    we monkeypatch that resolver. Async routers (plan / share / sequence /
    insights / pathway / simulate / barrier-intel chat / feedback /
    plan_intelligence) read the SQLAlchemy engine; we point the engine at
    the same SQLite file by overriding ``database_url`` and clearing the
    settings cache + engine globals.
    """
    from app.routes import _appointments_helpers as auth_helpers

    monkeypatch.setattr(
        auth_helpers, "resolve_db_path", lambda: two_session_db,
    )

    # Re-route the async engine to the same file. Lazy import so the
    # settings cache_clear lands before any first ``get_settings()`` call.
    from app.core import config as config_mod
    from app.core import database as db_mod

    monkeypatch.setenv(
        "DATABASE_URL", f"sqlite+aiosqlite:///{two_session_db}",
    )
    config_mod.get_settings.cache_clear()

    old_engine = db_mod._engine
    old_factory = db_mod._async_session_factory
    db_mod._engine = None
    db_mod._async_session_factory = None

    from app.main import app
    client = TestClient(app, raise_server_exceptions=False)
    try:
        yield client
    finally:
        db_mod._engine = old_engine
        db_mod._async_session_factory = old_factory
        config_mod.get_settings.cache_clear()


# --------------------------------------------------------------- helpers


def _build_request_args(spec: RouteSpec) -> dict[str, Any]:
    """Construct ``params`` / ``json`` for a cross-session call against ``spec``.

    The session_id slot is filled with sess-A; the token slot is filled
    with tok-B (which is valid but owned by sess-B). Required body
    fields outside auth get a deterministic placeholder so the request
    survives schema validation and reaches the ownership check.
    """
    url_path = spec.path.replace("{session_id}", _SESS_A)
    # Replace other path parameters with valid placeholders
    url_path = url_path.replace("{job_index}", "0")
    params: dict[str, Any] = {}
    body: dict[str, Any] | None = None

    if spec.session_id_loc == "query":
        params["session_id"] = _SESS_A
    elif spec.session_id_loc == "body":
        body = {"session_id": _SESS_A}

    if spec.token_loc == "query":
        params[spec.token_name] = _TOK_B
    elif spec.token_loc == "body":
        body = body if body is not None else {}
        body[spec.token_name] = _TOK_B

    if spec.body_required_fields:
        body = body if body is not None else {}
        for field_name in spec.body_required_fields:
            body.setdefault(
                field_name,
                REQUIRED_FIELD_PLACEHOLDERS.get(field_name, "x"),
            )

    return {"url": url_path, "params": params, "json": body}


def _expected_pass(status_code: int) -> bool:
    """403 is the contract; a body validation 422 is a noisy ok."""
    return status_code == 403


# --------------------------------------------------------------- tests


def test_inventory_discovers_at_least_one_session_route(
    isolation_client: TestClient,
) -> None:
    """Sanity: route discovery finds the well-known compliance/export path."""
    specs = discover_session_routes(isolation_client.app)
    paths_methods = {f"{s.method} {s.path}" for s in specs}
    assert "POST /api/compliance/export" in paths_methods
    assert "GET /api/insights/{session_id}" in paths_methods


def test_allowlist_only_references_real_endpoints(
    isolation_client: TestClient,
) -> None:
    """Every PUBLIC_ENDPOINTS entry must correspond to a live route.

    Catches typos and stale entries — an allowlist that drifts away from
    the real router gives a false sense of coverage.
    """
    real = {f"{m} {p}" for m, p in all_route_specs(isolation_client.app)}
    stale = sorted(set(PUBLIC_ENDPOINTS) - real)
    assert not stale, f"PUBLIC_ENDPOINTS references missing routes: {stale}"


def test_no_session_route_is_silently_allowlisted(
    isolation_client: TestClient,
) -> None:
    """A discovered session-owned route must never appear on the allowlist.

    Putting a session-owned endpoint on the allowlist would silently
    suppress its cross-session check. Force the allowlist to be reserved
    for routes the heuristic does NOT flag.
    """
    specs = discover_session_routes(isolation_client.app)
    flagged = {f"{s.method} {s.path}" for s in specs}
    overlap = sorted(flagged & set(PUBLIC_ENDPOINTS))
    assert not overlap, (
        f"Session-owned routes on allowlist (would skip ownership "
        f"check): {overlap}"
    )


def test_every_endpoint_is_either_flagged_or_allowlisted(
    isolation_client: TestClient,
) -> None:
    """Every (method, path) the app exposes must be triaged.

    A new endpoint that is neither flagged by the discovery heuristic
    nor explicitly allowlisted is a triage gap — the contributor must
    decide whether the route needs ownership testing or a documented
    exemption. This guard fails until that decision is recorded.
    """
    specs = discover_session_routes(isolation_client.app)
    flagged = {f"{s.method} {s.path}" for s in specs}
    all_routes = {
        f"{m} {p}" for m, p in all_route_specs(isolation_client.app)
    }
    untriaged = sorted(all_routes - flagged - set(PUBLIC_ENDPOINTS))
    assert not untriaged, (
        "New endpoints lack a cross-session decision — either fix "
        "ownership enforcement or add to PUBLIC_ENDPOINTS with a "
        f"reason:\n{untriaged}"
    )


@pytest.fixture
def session_route_specs(isolation_client: TestClient) -> list[RouteSpec]:
    """Cached list of session-owned route specs for the parametrize loop."""
    return discover_session_routes(isolation_client.app)


def test_every_session_route_returns_403_on_cross_session(
    isolation_client: TestClient,
    session_route_specs: list[RouteSpec],
) -> None:
    """For every flagged route: session-A id + session-B token -> 403.

    Failure messages name the offending endpoint so a regression points
    at the exact handler that lost its ownership check.
    """
    failures: list[str] = []
    with freeze_time(_FROZEN_INSTANT):
        for spec in session_route_specs:
            args = _build_request_args(spec)
            response = isolation_client.request(
                spec.method, args["url"],
                params=args["params"] or None,
                json=args["json"],
            )
            if _expected_pass(response.status_code):
                continue
            failures.append(
                f"{spec.method} {spec.path} -> {response.status_code} "
                f"(expected 403). body={response.text[:200]!r}",
            )
    assert not failures, (
        "Cross-session isolation broken on the following endpoints:\n"
        + "\n".join(failures)
    )


def test_known_route_returns_403_smoke(
    isolation_client: TestClient,
) -> None:
    """One pinned-down sanity case: compliance/export with cross-session token."""
    response = isolation_client.post(
        "/api/compliance/export",
        json={"session_id": _SESS_A, "session_token": _TOK_B},
    )
    assert response.status_code == 403, response.text
