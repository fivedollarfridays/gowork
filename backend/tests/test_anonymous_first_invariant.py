"""Anonymous-first invariant — every session-id route works without an account.

The contract under test
=======================

GoWork is **anonymous-first**: a worker can use the entire product without
ever creating an account. T22.5 added the ability to *claim* an anonymous
``sessions.id`` row by binding it to an account through
``account_sessions``, but binding a session must NEVER change what the
backend serves to the caller. Every endpoint that takes a ``session_id``
must produce the same response shape and the same HTTP status whether the
session is anonymous (no row in ``account_sessions``) or claimed (a row in
``account_sessions`` linking it to an account).

This test is the load-bearing guard that prevents future drift toward
forced-login. A new endpoint that gates behavior on "is this session
claimed?" — without going through a documented allowlist amendment — will
make this test fail loudly with the offending endpoint named.

Endpoint discovery
==================

Routes are enumerated from the live ``app.routes`` (FastAPI introspection
in :mod:`tests._route_inventory`) — there is no hand-maintained list. Any
route whose endpoint signature or declared body model includes both a
``session_id`` and a session-bound ``token`` / ``session_token`` parameter
is automatically picked up. Routes that legitimately gate on auth go on
:data:`REQUIRES_AUTH_ALLOWLIST` with a one-line rationale. Routes whose
required body shape is too entangled for a generic test go on
:data:`SKIPPED_FOR_BODY_COMPLEXITY` — they are still covered by their own
dedicated test file.

Allowed response differences
============================

Account-aware fields legitimately differ between anonymous and claimed
calls (today none exist; the allowlist exists so future additions are
explicitly opt-in rather than silent drift). Only the field names in
:data:`ALLOWED_DIFF_FIELDS` may differ between the two responses.

Ephemeral server-generated fields (timestamps, generated tokens, autoincr
ids) are normalized away in :func:`_normalize_response` before comparison
so the diff highlights only behavioral drift, not non-determinism.

Charter linkage
===============

The integrity charter (``docs/integrity-charter.draft.md``) commits GoWork
to keeping the matching engine and the candidate-side product accessible
without paying, without subscribing, and — by extension — without forced
authentication. This test is the executable form of that commitment for
the API surface.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.migrations import runner
from tests._cross_session_fixtures import REQUIRED_FIELD_PLACEHOLDERS
from tests._fake_clock import freeze_time
from tests._route_inventory import RouteSpec, discover_session_routes


# --------------------------------------------------------------- constants


#: Field names that are allowed to differ between anonymous and claimed
#: responses. Today this is empty in spirit (no route returns
#: account-aware fields yet), but the slots are reserved so the day a
#: route legitimately surfaces account context the contributor only has
#: to extend this list with a rationale.
ALLOWED_DIFF_FIELDS: frozenset[str] = frozenset({"account_id", "account_email"})


#: Routes that intentionally gate on authentication. Every entry MUST
#: carry a one-line rationale; a route added here without rationale will
#: fail review. As of T22.9 this is empty — the sprint charter forbids
#: any endpoint from forcing login. Admin / advisor surfaces use a
#: different trust boundary and are not flagged by the discovery
#: heuristic, so they don't appear here either.
REQUIRES_AUTH_ALLOWLIST: dict[str, str] = {}


#: Routes whose required body shape pulls in domain validation that's
#: too entangled to satisfy with a generic placeholder. Each entry MUST
#: name the dedicated test file that covers it. The invariant guard
#: still asserts these endpoints exist (so a typo here is caught), it
#: just doesn't exercise them.
SKIPPED_FOR_BODY_COMPLEXITY: dict[str, str] = {
    # ``barrier-intel/chat`` runs the LLM router with a closed-enum
    # ``mode`` and a free-text question; the response shape is dynamic
    # and exercising it requires the haiku/test fixture stack already
    # set up in test_barrier_intel_router.py.
    "POST /api/barrier-intel/chat":
        "LLM-driven; full coverage in test_barrier_intel_router.py.",
    # ``documents/cover-letter`` requires a pre-existing resume version
    # row referenced by id; the equality check is fully covered in
    # test_documents_routes.py against properly seeded resume data.
    "POST /api/documents/cover-letter":
        "Requires pre-seeded resume_version_id; covered in "
        "test_documents_routes.py.",
}


# UUID-shaped ids: several routes (plan, simulate, pathway, insights,
# barrier-intel chat, feedback) declare ``session_id`` with a strict
# UUID regex so a non-UUID input never reaches the auth check. We
# reuse the same UUID shape as the cross-session test for consistency.
_SESS_ANON = "11111111-1111-1111-1111-111111111111"
_SESS_CLAIMED = "22222222-2222-2222-2222-222222222222"
_TOK_ANON = "tok-anon-aaaaaaaaaaaaaaaaaaaaaaaaaaaa"
_TOK_CLAIMED = "tok-claimed-bbbbbbbbbbbbbbbbbbbbbbbbb"
_FROZEN_INSTANT = "2026-05-06T12:00:00+00:00"


#: Keys that vary between the two calls for a reason unrelated to the
#: anonymous-first invariant: either server-generated and
#: non-deterministic (timestamps, autoincr ids, generated tokens), or
#: input-echoed (``session_id`` itself, the auth ``token``). Stripped
#: from both responses recursively before comparison so the diff
#: flags only real behavioral drift.
_EPHEMERAL_KEYS: frozenset[str] = frozenset(
    {
        # Input echoes — necessarily differ between the two calls.
        "session_id",
        "token",
        "session_token",
        # Server-generated, non-deterministic across calls.
        "share_token",
        "url",
        "id",
        "created_at",
        "updated_at",
        "submitted_at",
        "generated_at",
        "expires_at",
        "appointment_id",
        "version_id",
        "application_id",
    }
)


# --------------------------------------------------------------- fixtures


@pytest.fixture
def two_session_db(tmp_path: Path) -> str:
    """Migrated SQLite DB with two sessions, two tokens, one claimed.

    Layout:

    * ``_SESS_ANON``   — anonymous (no row in ``account_sessions``)
    * ``_SESS_CLAIMED`` — claimed by the test account in
      ``account_sessions``
    * ``_TOK_ANON``    — feedback token owned by ``_SESS_ANON``
    * ``_TOK_CLAIMED`` — feedback token owned by ``_SESS_CLAIMED``

    Both sessions are otherwise identical (same plan blob, same
    barriers) so any response divergence is attributable to the
    claim binding, not to seed-data drift.
    """
    db_path = str(tmp_path / "anon_first.db")
    runner.apply_pending(db_path)
    _apply_accounts_ddl_sync(db_path)
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        _seed_sessions_and_tokens(conn, now.isoformat(), expires)
        _seed_account_and_claim(conn, now.isoformat())
        conn.commit()
    finally:
        conn.close()
    return db_path


def _apply_accounts_ddl_sync(db_path: str) -> None:
    """Run the identity-layer DDL on the sync sqlite connection.

    The legacy migration runner stops at m010; alembic 0011 owns the
    identity tables. We mirror what ``test_accounts.py`` does — apply
    the DDL via SQLAlchemy on top of the legacy schema — but on a sync
    connection so the seed phase below can stay sqlite3-only.
    """
    from sqlalchemy import create_engine
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        apply_accounts_ddl(conn)
    engine.dispose()


def _seed_sessions_and_tokens(
    conn: sqlite3.Connection, now_iso: str, expires_iso: str,
) -> None:
    """Insert two identical sessions and one feedback token per session."""
    for sid in (_SESS_ANON, _SESS_CLAIMED):
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, profile, "
            "expires_at) VALUES (?, ?, ?, ?, ?)",
            (sid, now_iso, "[]", "{}", expires_iso),
        )
    for tok, sid in ((_TOK_ANON, _SESS_ANON), (_TOK_CLAIMED, _SESS_CLAIMED)):
        conn.execute(
            "INSERT INTO feedback_tokens "
            "(token, session_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (tok, sid, now_iso, expires_iso),
        )


def _seed_account_and_claim(
    conn: sqlite3.Connection, now_iso: str,
) -> None:
    """Insert one account and claim ``_SESS_CLAIMED`` for it."""
    conn.execute(
        "INSERT INTO accounts (email, created_at, last_active_at) "
        "VALUES (?, ?, ?)",
        ("anon-first-test@example.com", now_iso, now_iso),
    )
    cursor = conn.execute(
        "SELECT id FROM accounts WHERE email = ?",
        ("anon-first-test@example.com",),
    )
    account_id = cursor.fetchone()[0]
    conn.execute(
        "INSERT INTO account_sessions "
        "(account_id, session_id, claimed_at) VALUES (?, ?, ?)",
        (account_id, _SESS_CLAIMED, now_iso),
    )


@pytest.fixture
def invariant_client(
    two_session_db: str, monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    """TestClient wired to the two-session DB (sync + async routers).

    Mirrors the wiring in :mod:`test_cross_session_isolation` so this
    test exercises the same endpoint surface against the same backing
    store. Sync routers go through ``resolve_db_path`` (monkeypatched);
    async routers go through the SQLAlchemy engine (re-created via the
    ``DATABASE_URL`` override).

    Rate-limiter hygiene
    --------------------
    This test calls every session-id route TWICE (anon + claimed) which
    is enough to exhaust the in-process rate limiters (e.g.
    ``plan._rate_limiter`` allows 5 calls/min). We reset the relevant
    limiters on entry and exit so neighbouring tests don't see leaked
    state — the cross-session test in particular re-hits the same
    endpoints from the same TestClient IP.
    """
    from app.routes import _appointments_helpers as auth_helpers

    monkeypatch.setattr(
        auth_helpers, "resolve_db_path", lambda: two_session_db,
    )

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

    _reset_known_rate_limiters()
    from app.main import app
    client = TestClient(app, raise_server_exceptions=False)
    try:
        yield client
    finally:
        _reset_known_rate_limiters()
        db_mod._engine = old_engine
        db_mod._async_session_factory = old_factory
        config_mod.get_settings.cache_clear()


def _reset_known_rate_limiters() -> None:
    """Clear in-process rate limiter state on every route module.

    Each route module declares its own module-level ``_rate_limiter``
    (or differently-named limiter). We dynamically introspect the
    routes package to find every ``RateLimiter`` instance and clear it
    — that way a future router gets the same hygiene without anyone
    editing this list.
    """
    from app.core.rate_limit import RateLimiter
    from app.routes import (
        assessment, credit, documents, feedback, jobs, plan, share,
    )
    for module in (assessment, credit, documents, feedback, jobs, plan, share):
        for name in dir(module):
            obj = getattr(module, name, None)
            if isinstance(obj, RateLimiter):
                obj.clear()


@pytest.fixture
def session_route_specs(invariant_client: TestClient) -> list[RouteSpec]:
    """Cached list of session-owned route specs for the parametrize loop."""
    return discover_session_routes(invariant_client.app)


# --------------------------------------------------------------- helpers


def _build_request_args(
    spec: RouteSpec, session_id: str, token: str,
) -> dict[str, Any]:
    """Construct ``url`` / ``params`` / ``json`` for a single route call.

    Same shape as :func:`tests.test_cross_session_isolation._build_request_args`
    but with caller-supplied session id and token so the helper can be
    invoked twice (anon, claimed) per route.
    """
    url_path = spec.path.replace("{session_id}", session_id)
    url_path = url_path.replace("{job_index}", "0")
    params: dict[str, Any] = {}
    body: dict[str, Any] | None = None

    if spec.session_id_loc == "query":
        params["session_id"] = session_id
    elif spec.session_id_loc == "body":
        body = {"session_id": session_id}

    if spec.token_loc == "query":
        params[spec.token_name] = token
    elif spec.token_loc == "body":
        body = body if body is not None else {}
        body[spec.token_name] = token

    if spec.body_required_fields:
        body = body if body is not None else {}
        for field_name in spec.body_required_fields:
            body.setdefault(
                field_name,
                REQUIRED_FIELD_PLACEHOLDERS.get(field_name, "x"),
            )

    return {"url": url_path, "params": params, "json": body}


def _normalize_response(payload: Any) -> Any:
    """Strip ephemeral and account-allowlisted keys recursively.

    Two responses that differ only in ephemeral fields (auto-generated
    ids, server timestamps) or in :data:`ALLOWED_DIFF_FIELDS` should
    compare as equivalent — the invariant cares about response *shape*
    and *behavior*, not the exact bytes of a generated UUID.
    """
    if isinstance(payload, dict):
        return {
            k: _normalize_response(v)
            for k, v in payload.items()
            if k not in _EPHEMERAL_KEYS and k not in ALLOWED_DIFF_FIELDS
        }
    if isinstance(payload, list):
        return [_normalize_response(item) for item in payload]
    return payload


def _decode_body(response: Any) -> Any:
    """Decode response body as JSON, falling back to raw text."""
    try:
        return response.json()
    except (ValueError, TypeError):
        return response.text


def _route_key(spec: RouteSpec) -> str:
    """Return the canonical ``"METHOD /path"`` allowlist key."""
    return f"{spec.method} {spec.path}"


def _call_route(
    client: TestClient, spec: RouteSpec, session_id: str, token: str,
) -> tuple[int, Any]:
    """Issue a single request for ``spec`` and return (status, normalized)."""
    args = _build_request_args(spec, session_id, token)
    response = client.request(
        spec.method, args["url"],
        params=args["params"] or None,
        json=args["json"],
    )
    return response.status_code, _normalize_response(_decode_body(response))


def _is_skipped(spec: RouteSpec) -> bool:
    """Return True if ``spec`` is on either the auth or body allowlist."""
    key = _route_key(spec)
    return key in REQUIRES_AUTH_ALLOWLIST or key in SKIPPED_FOR_BODY_COMPLEXITY


# --------------------------------------------------------------- tests


def test_inventory_finds_at_least_thirty_session_routes(
    session_route_specs: list[RouteSpec],
) -> None:
    """Sanity floor: route discovery surfaces the known ~30 session routes.

    A regression here (e.g., a router accidentally dropped from
    ``app.routes.__init__``) would make every other assertion in this
    module vacuously pass. Anchor the count so a missed router fails
    loudly with a recognizable message.
    """
    assert len(session_route_specs) >= 30, (
        f"Expected at least 30 session-owned routes, "
        f"found {len(session_route_specs)}. Did a router get unwired?"
    )


def test_allowlists_only_reference_real_endpoints(
    session_route_specs: list[RouteSpec],
) -> None:
    """Both allowlists must reference live (METHOD, path) pairs.

    Catches typos and stale entries — an allowlist that drifts away
    from the real router gives a false sense of coverage.
    """
    real = {_route_key(s) for s in session_route_specs}
    stale_auth = sorted(set(REQUIRES_AUTH_ALLOWLIST) - real)
    stale_body = sorted(set(SKIPPED_FOR_BODY_COMPLEXITY) - real)
    assert not stale_auth, (
        f"REQUIRES_AUTH_ALLOWLIST references missing routes: "
        f"{stale_auth}"
    )
    assert not stale_body, (
        f"SKIPPED_FOR_BODY_COMPLEXITY references missing routes: "
        f"{stale_body}"
    )


def test_anonymous_first_invariant_holds_for_every_session_route(
    invariant_client: TestClient,
    session_route_specs: list[RouteSpec],
) -> None:
    """Each session-id route returns equivalent shape for anon and claimed.

    The body of the assertion is per-endpoint so a regression points at
    the exact handler that started gating on ``account_sessions``.
    """
    failures: list[str] = []
    covered = 0
    with freeze_time(_FROZEN_INSTANT):
        for spec in session_route_specs:
            if _is_skipped(spec):
                continue
            covered += 1
            anon_status, anon_body = _call_route(
                invariant_client, spec, _SESS_ANON, _TOK_ANON,
            )
            claimed_status, claimed_body = _call_route(
                invariant_client, spec, _SESS_CLAIMED, _TOK_CLAIMED,
            )
            failure = _diff_responses(
                spec, anon_status, anon_body,
                claimed_status, claimed_body,
            )
            if failure:
                failures.append(failure)

    assert not failures, (
        "Anonymous-first invariant broken on the following endpoints "
        "(claimed sessions diverged from anonymous sessions):\n"
        + "\n".join(failures)
    )
    # Floor: at least 25 endpoints actually exercised end-to-end.
    # Anything less means the skip lists swallowed too much coverage.
    assert covered >= 25, (
        f"Only {covered} routes actually compared anon-vs-claimed; "
        f"too many endpoints on SKIPPED_FOR_BODY_COMPLEXITY "
        f"or REQUIRES_AUTH_ALLOWLIST."
    )


def _diff_responses(
    spec: RouteSpec,
    anon_status: int, anon_body: Any,
    claimed_status: int, claimed_body: Any,
) -> str | None:
    """Return a human-readable failure string, or None when equivalent."""
    if anon_status != claimed_status:
        return (
            f"{_route_key(spec)} -> status diverged: "
            f"anon={anon_status} claimed={claimed_status} "
            f"anon_body={str(anon_body)[:120]!r} "
            f"claimed_body={str(claimed_body)[:120]!r}"
        )
    if anon_body != claimed_body:
        return (
            f"{_route_key(spec)} -> body diverged at status "
            f"{anon_status}: anon={str(anon_body)[:160]!r} "
            f"claimed={str(claimed_body)[:160]!r}"
        )
    return None


def test_known_route_returns_equivalent_smoke(
    invariant_client: TestClient,
) -> None:
    """One pinned-down sanity case: GET /api/insights/{sid} matches.

    A whole-suite regression that swallows every diff into a single
    failure list could miss a single-endpoint break. This smoke test
    asserts the most common GET happy-path independently so a future
    refactor of the diff loop still has a load-bearing guard.
    """
    args_anon = {"params": {"token": _TOK_ANON}}
    args_claimed = {"params": {"token": _TOK_CLAIMED}}
    with freeze_time(_FROZEN_INSTANT):
        anon = invariant_client.get(
            f"/api/insights/{_SESS_ANON}", **args_anon,
        )
        claimed = invariant_client.get(
            f"/api/insights/{_SESS_CLAIMED}", **args_claimed,
        )
    assert anon.status_code == claimed.status_code, (
        f"Insights status diverged: anon={anon.status_code} "
        f"claimed={claimed.status_code}"
    )
    assert _normalize_response(anon.json()) == _normalize_response(
        claimed.json(),
    ), "Insights body diverged between anon and claimed"
