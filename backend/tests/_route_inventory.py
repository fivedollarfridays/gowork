"""Route inventory + classification for cross-session isolation tests (T13.63).

Walks the live FastAPI ``app.routes`` and classifies each ``APIRoute`` by
how it authenticates the caller. The cross-session isolation test relies
on this classification to drive request construction — so a newly added
endpoint that accepts a session token will automatically be picked up
and tested without anyone editing the test file.

Detection heuristic
-------------------
A route is classified as **session-owned** when its endpoint signature
or its declared body model includes both:

* a ``session_id`` parameter (path / query / body field), AND
* a ``token`` or ``session_token`` parameter (query / body field).

Routes with neither, with admin headers (``x_admin_key``), with only a
signed manage / share / unsubscribe token (no ``session_id`` companion),
or with an ``advisor`` dependency are NOT classified as session-owned —
they live behind a different auth model and are covered by their own
test files.

Returning a structured ``RouteSpec`` (rather than just the path/method)
keeps the assertion driver simple: it knows where to inject the
session_id and the token without re-introspecting the route.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute


# Names that indicate a session-id parameter — always exact match.
_SESSION_ID_NAMES: frozenset[str] = frozenset({"session_id"})

# Names that indicate a session-bound token parameter.
_TOKEN_NAMES: frozenset[str] = frozenset({"token", "session_token"})


@dataclass(frozen=True)
class RouteSpec:
    """Minimal description of one HTTP method on one path."""

    method: str
    path: str
    # Where each well-known parameter lives ('path' / 'query' / 'body').
    session_id_loc: str
    token_loc: str
    token_name: str  # 'token' or 'session_token'
    # Body field names (used to fill required non-auth fields).
    body_required_fields: tuple[str, ...] = field(default_factory=tuple)


def discover_session_routes(app: FastAPI) -> list[RouteSpec]:
    """Return one RouteSpec per (method, path) that requires session ownership.

    See module docstring for the detection heuristic. The list is sorted
    by ``(path, method)`` for deterministic test ordering.
    """
    specs: list[RouteSpec] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path_param_names = _path_param_names(route.path)
        sig_params = _signature_params(route.endpoint)
        body_fields = _body_fields(route)
        body_required = _required_body_fields(route)

        sid_loc = _locate(
            _SESSION_ID_NAMES,
            path_param_names, sig_params, body_fields,
        )
        if sid_loc is None:
            continue

        tok_name, tok_loc = _locate_token(
            sig_params, body_fields,
        )
        if tok_loc is None:
            continue

        for method in sorted(route.methods or ()):
            if method in {"HEAD", "OPTIONS"}:
                continue
            specs.append(
                RouteSpec(
                    method=method,
                    path=route.path,
                    session_id_loc=sid_loc,
                    token_loc=tok_loc,
                    token_name=tok_name,
                    body_required_fields=tuple(body_required),
                ),
            )
    specs.sort(key=lambda s: (s.path, s.method))
    return specs


def all_route_specs(app: FastAPI) -> list[tuple[str, str]]:
    """Every (method, path) pair the app exposes — used by the allowlist guard.

    Lets the allowlist enforcement step distinguish "this endpoint is on
    the allowlist but does not exist" (typo) from "this endpoint exists
    but is not on the allowlist and does not require ownership" (gap).
    """
    out: list[tuple[str, str]] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(route.methods or ()):
            if method in {"HEAD", "OPTIONS"}:
                continue
            out.append((method, route.path))
    out.sort()
    return out


# -------------------- internals --------------------


def _path_param_names(path: str) -> set[str]:
    """Return the brace-wrapped param names from a FastAPI path template."""
    out: set[str] = set()
    i = 0
    while i < len(path):
        if path[i] == "{":
            close = path.find("}", i)
            if close == -1:
                break
            out.add(path[i + 1: close].split(":", 1)[0])
            i = close + 1
        else:
            i += 1
    return out


def _signature_params(endpoint: Any) -> dict[str, inspect.Parameter]:
    """Endpoint callable signature parameters, keyed by name."""
    try:
        sig = inspect.signature(endpoint)
    except (TypeError, ValueError):
        return {}
    return dict(sig.parameters)


def _body_fields(route: APIRoute) -> set[str]:
    """Return all field names declared on the route's body model."""
    bf = route.body_field
    if bf is None:
        return set()
    try:
        annotation = bf.field_info.annotation
    except AttributeError:
        return set()
    fields = getattr(annotation, "model_fields", None)
    if not fields:
        return set()
    return set(fields.keys())


def _required_body_fields(route: APIRoute) -> list[str]:
    """Return only required (no-default) body fields, excluding auth fields."""
    bf = route.body_field
    if bf is None:
        return []
    try:
        annotation = bf.field_info.annotation
    except AttributeError:
        return []
    model_fields = getattr(annotation, "model_fields", None)
    if not model_fields:
        return []
    out: list[str] = []
    for name, finfo in model_fields.items():
        if name in _SESSION_ID_NAMES or name in _TOKEN_NAMES:
            continue
        if getattr(finfo, "is_required", lambda: True)():
            out.append(name)
    return out


def _locate(
    targets: frozenset[str],
    path_params: set[str],
    sig_params: dict[str, inspect.Parameter],
    body_fields: set[str],
) -> str | None:
    """Return where a ``targets`` parameter lives, or ``None`` if absent."""
    for name in targets:
        if name in path_params:
            return "path"
        if name in body_fields:
            return "body"
        if name in sig_params:
            return "query"
    return None


def _locate_token(
    sig_params: dict[str, inspect.Parameter],
    body_fields: set[str],
) -> tuple[str, str | None]:
    """Locate the session-bound token; returns (chosen_name, location)."""
    # Prefer body-side ``session_token`` (compliance pattern) before
    # falling back to query-side ``token``.
    if "session_token" in body_fields:
        return "session_token", "body"
    if "token" in body_fields:
        return "token", "body"
    if "token" in sig_params:
        return "token", "query"
    return "token", None


__all__ = ["RouteSpec", "all_route_specs", "discover_session_routes"]
