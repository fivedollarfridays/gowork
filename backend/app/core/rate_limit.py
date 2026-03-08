"""Shared in-memory rate limiter."""

import time

from fastapi import HTTPException, Request

from app.core.audit import get_client_ip


class RateLimiter:
    """Simple in-memory rate limiter: max_requests per window_seconds per key."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._call_count = 0

    def check(self, key: str) -> bool:
        """Return True if under limit, False if over."""
        now = time.monotonic()
        cutoff = now - self._window
        timestamps = self._requests.get(key, [])
        timestamps = [t for t in timestamps if t > cutoff]
        if len(timestamps) >= self._max:
            self._requests[key] = timestamps
            return False
        timestamps.append(now)
        self._requests[key] = timestamps
        self._call_count += 1
        if self._call_count % 100 == 0:
            self._prune_stale(cutoff)
        return True

    def _prune_stale(self, cutoff: float) -> None:
        """Remove keys with no recent timestamps."""
        stale = [k for k, v in self._requests.items() if not v or v[-1] <= cutoff]
        for k in stale:
            del self._requests[k]

    def clear(self) -> None:
        """Reset all tracked requests (for testing)."""
        self._requests.clear()
        self._call_count = 0


def require_rate_limit(limiter: RateLimiter):
    """FastAPI dependency factory for rate limiting."""
    async def _check(request: Request) -> None:
        client_ip = get_client_ip(request)
        if not limiter.check(client_ip):
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    return _check
