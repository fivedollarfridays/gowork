"""In-memory TTL caching for barrier intelligence responses and retrieval."""

import hashlib
from typing import Any

from cachetools import TTLCache

# LLM response cache: 5 min TTL, max 200 entries
RESPONSE_CACHE: TTLCache = TTLCache(maxsize=200, ttl=300)

# Retrieval context cache: 10 min TTL, max 500 entries
RETRIEVAL_CACHE: TTLCache = TTLCache(maxsize=500, ttl=600)


def get_cache_key(session_id: str, question: str, mode: str) -> str:
    """Generate a deterministic cache key from request parameters."""
    raw = f"{session_id}:{question}:{mode}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_cached_response(key: str) -> Any | None:
    """Get a cached LLM response, or None on miss."""
    return RESPONSE_CACHE.get(key)


def set_cached_response(key: str, value: Any) -> None:
    """Store an LLM response in the cache."""
    RESPONSE_CACHE[key] = value


def get_cached_retrieval(key: str) -> Any | None:
    """Get cached retrieval context, or None on miss."""
    return RETRIEVAL_CACHE.get(key)


def set_cached_retrieval(key: str, value: Any) -> None:
    """Store retrieval context in the cache."""
    RETRIEVAL_CACHE[key] = value
