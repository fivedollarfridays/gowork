"""Tiny TTL-bounded in-memory cache for Haiku responses.

We don't need Redis for the hackathon; one process, modest call volume.
Each cache is a singleton keyed by (namespace, key) -> (expires_at, value).
"""

from __future__ import annotations

import threading
import time
from typing import Generic, TypeVar

V = TypeVar("V")


class TTLCache(Generic[V]):
    """Thread-safe TTL cache.

    Entries auto-expire on read; no background sweeper.  Bounded by
    ``max_entries`` — when full, the oldest entry by insertion time is
    evicted.  Designed for ~thousands of entries, not millions.
    """

    def __init__(self, *, default_ttl_s: float, max_entries: int = 2000) -> None:
        self._ttl = float(default_ttl_s)
        self._max = int(max_entries)
        self._data: dict[str, tuple[float, V]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> V | None:
        """Return cached value, or None if missing/expired."""
        now = time.time()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < now:
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: V, ttl_s: float | None = None) -> None:
        """Cache a value with optional explicit TTL."""
        ttl = float(ttl_s) if ttl_s is not None else self._ttl
        expires_at = time.time() + ttl
        with self._lock:
            if len(self._data) >= self._max and key not in self._data:
                # Evict oldest by insertion order (dict preserves it)
                try:
                    oldest = next(iter(self._data))
                    self._data.pop(oldest, None)
                except StopIteration:
                    pass
            self._data[key] = (expires_at, value)

    def clear(self) -> None:
        """Drop all entries.  Test helper."""
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)


# 24h TTL for match explanations — plans rarely change in a session window.
match_explanation_cache: TTLCache[str] = TTLCache(default_ttl_s=86400, max_entries=2000)

# 90d TTL for job description summaries — descriptions are mostly stable
# once posted.  Cache purges naturally when listings churn.
job_summary_cache: TTLCache[dict] = TTLCache(default_ttl_s=86400 * 90, max_entries=5000)

# 24h TTL for next-step plan composition — keyed by session_id.
next_step_cache: TTLCache[list] = TTLCache(default_ttl_s=86400, max_entries=2000)

# 7d TTL for Spanish polish — keyed by hash of source text.
spanish_polish_cache: TTLCache[dict] = TTLCache(default_ttl_s=86400 * 7, max_entries=2000)
