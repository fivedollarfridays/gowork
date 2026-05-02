"""Mapbox forward-geocoding client (server-side).

Single function, one call per address, fail-soft. The frontend already
ships a public Mapbox token in ``frontend/.env.local.example``; the same
token works server-side via the REST geocoding endpoint.

Token resolution
----------------
1. ``MAPBOX_TOKEN`` (preferred for backend)
2. ``NEXT_PUBLIC_MAPBOX_TOKEN`` (fallback — same token shipped to the
   browser)
3. Neither set -> :func:`geocode_address` returns ``None`` and logs a
   single ``WARNING`` per process.

Failure policy
--------------
Every error path collapses to ``None``: timeouts, 4xx/5xx, empty
features, malformed payloads. The caller (backfill script + scoring
hook) treats ``None`` as "no distance signal" and degrades gracefully.
**Never** invent coordinates.
"""
from __future__ import annotations

import logging
import os
from typing import Optional
from urllib.parse import quote

import httpx

from app.integrations._http_retry import async_get_with_retry

_logger = logging.getLogger(__name__)

_MAPBOX_GEOCODE_BASE = "https://api.mapbox.com/geocoding/v5/mapbox.places"

# DFW proximity hint (downtown Fort Worth) biases ranking toward the
# active service area without restricting matches.
_DFW_PROXIMITY = "-97.32,32.75"

# Per-call HTTP timeout. Mapbox is fast; 30s is a generous ceiling and
# matches the dispatch.
_TIMEOUT_SECONDS = 30.0

# Retries are handled by ``async_get_with_retry`` (3 attempts,
# exponential backoff). We only need to surface the response.
_MAX_ATTEMPTS = 3

# Module-level guard: log the "no token configured" warning at most
# once per process so the backfill script (which calls geocode_address
# in a loop) doesn't flood logs when the operator forgot to set the
# env var.
_no_token_warning_logged = False


def _reset_no_token_warning() -> None:  # pragma: no cover - test helper
    """Reset the once-per-process warning flag (test seam)."""
    global _no_token_warning_logged
    _no_token_warning_logged = False


def _resolve_token() -> Optional[str]:
    """Pick a Mapbox token from env, preferring server-side var name."""
    token = os.environ.get("MAPBOX_TOKEN")
    if token:
        return token.strip() or None
    fallback = os.environ.get("NEXT_PUBLIC_MAPBOX_TOKEN")
    if fallback:
        return fallback.strip() or None
    return None


def _warn_missing_token_once() -> None:
    """Log the no-token warning at most once per process."""
    global _no_token_warning_logged
    if _no_token_warning_logged:
        return
    _no_token_warning_logged = True
    _logger.warning(
        "MAPBOX_TOKEN (or NEXT_PUBLIC_MAPBOX_TOKEN) is not set; "
        "geocoding disabled — distance scoring will degrade to None.",
    )


def _build_url(address: str, token: str) -> str:
    """Compose the forward-geocoding URL with US country bias + DFW
    proximity hint + address-only types."""
    encoded = quote(address, safe="")
    return (
        f"{_MAPBOX_GEOCODE_BASE}/{encoded}.json"
        f"?access_token={token}"
        f"&country=US"
        f"&proximity={_DFW_PROXIMITY}"
        f"&types=address"
        f"&limit=1"
    )


def _extract_lat_lng(payload: dict) -> Optional[tuple[float, float]]:
    """Pull (lat, lng) from the first feature's center, or None."""
    features = payload.get("features") or []
    if not features:
        return None
    center = features[0].get("center")
    if not center or len(center) < 2:
        return None
    lng, lat = center[0], center[1]
    try:
        return float(lat), float(lng)
    except (TypeError, ValueError):
        return None


async def _fetch_geocode(url: str, address: str) -> Optional[httpx.Response]:
    """Issue the GET, return the response on 2xx or ``None`` on any
    failure path."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await async_get_with_retry(
                client, url, max_attempts=_MAX_ATTEMPTS,
            )
    except httpx.HTTPError as exc:
        _logger.warning("mapbox geocode failed for %r: %s", address, exc)
        return None
    except Exception as exc:  # pragma: no cover - defensive
        _logger.warning(
            "mapbox geocode unexpected error for %r: %s", address, exc,
        )
        return None
    if resp.status_code != 200:
        _logger.warning(
            "mapbox geocode HTTP %d for %r", resp.status_code, address,
        )
        return None
    return resp


async def geocode_address(address: str) -> Optional[tuple[float, float]]:
    """Geocode *address* via Mapbox; return ``(lat, lng)`` or ``None``.

    Fails soft — any error path (no token, timeout, non-2xx, empty
    result, malformed payload) returns ``None``. Never raises.
    """
    if not address or not address.strip():
        return None
    token = _resolve_token()
    if not token:
        _warn_missing_token_once()
        return None
    url = _build_url(address.strip(), token)
    resp = await _fetch_geocode(url, address)
    if resp is None:
        return None
    try:
        payload = resp.json()
    except ValueError:
        _logger.warning("mapbox geocode: non-JSON body for %r", address)
        return None
    return _extract_lat_lng(payload)
