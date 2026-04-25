"""Internal retry helper for idempotent outbound HTTP GET requests.

Used by the BrightData / USAJobs / TWC integrations and any future
read-only adapter. Retry policy:

* Retries on:
    - ``httpx.ConnectError`` / ``httpx.ReadError`` / ``httpx.ReadTimeout``
    - 5xx responses (502, 503, 504, …)
* Does NOT retry on:
    - 4xx responses (caller's problem; surface immediately)
    - Successful 2xx / informational 1xx / 3xx responses
    - Non-network exceptions (programmer error)

POST/PATCH/DELETE callers must NOT use this helper — they should call
``client.post(...)`` directly so a transient failure is surfaced
instead of silently retried (T13.92 acceptance criterion).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

_logger = logging.getLogger(__name__)

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BASE_DELAY = 0.5  # seconds; exponential: 0.5, 1.0, 2.0


class NoRetry5xxError(httpx.HTTPError):
    """Raised when all retries are exhausted with persistent 5xx.

    Carries the last :class:`httpx.Response` so callers can extract
    upstream body text for log lines or surfaced error messages.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        last_response: httpx.Response | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.last_response = last_response


_RETRYABLE_NETWORK_ERRORS = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.ConnectTimeout,
)


def _backoff_delay(base_delay: float, attempt: int) -> float:
    """Exponential backoff: base, 2*base, 4*base, …"""
    return base_delay * (2 ** (attempt - 1))


async def _try_get_once(
    client: httpx.AsyncClient, url: str, kwargs: dict[str, Any],
) -> tuple[httpx.Response | None, Exception | None]:
    """Single GET attempt. Returns (response, network_exc) — exactly one set."""
    try:
        return await client.get(url, **kwargs), None
    except _RETRYABLE_NETWORK_ERRORS as exc:
        return None, exc


def _final_5xx_error(url: str, resp: httpx.Response, attempts: int) -> NoRetry5xxError:
    return NoRetry5xxError(
        resp.status_code,
        f"GET {url} returned {resp.status_code} after {attempts} attempts",
        last_response=resp,
    )


async def async_get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    base_delay: float = _DEFAULT_BASE_DELAY,
    **kwargs: Any,
) -> httpx.Response:
    """Issue an idempotent GET with exponential backoff.

    See module docstring for the retry policy. Raises
    :class:`NoRetry5xxError` on persistent 5xx; re-raises the original
    ``httpx`` network exception on persistent connection failure.
    """
    for attempt in range(1, max_attempts + 1):
        resp, net_exc = await _try_get_once(client, url, kwargs)
        if net_exc is not None:
            _logger.warning(
                "outbound GET %s: network error attempt %d/%d: %s",
                url, attempt, max_attempts, net_exc,
            )
            if attempt >= max_attempts:
                raise net_exc
            await asyncio.sleep(_backoff_delay(base_delay, attempt))
            continue
        assert resp is not None  # narrow for type checker
        if resp.status_code < 500:
            return resp  # 1xx / 2xx / 3xx / 4xx — no retry.
        _logger.warning(
            "outbound GET %s: %d attempt %d/%d",
            url, resp.status_code, attempt, max_attempts,
        )
        if attempt >= max_attempts:
            raise _final_5xx_error(url, resp, max_attempts)
        await asyncio.sleep(_backoff_delay(base_delay, attempt))
    raise AssertionError("unreachable")  # pragma: no cover
