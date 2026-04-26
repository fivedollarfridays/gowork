"""Shared kid whitelist for HMAC-signed token modules.

Each token module (appointments, compliance/_export, engagement/unsubscribe)
accepts only "current" or "old" as the kid value to prevent the
accept-any-kid downgrade vector closed by T13.62 + Wave 4 follow-up.
"""
from __future__ import annotations

KNOWN_KIDS: frozenset[str] = frozenset({"current", "old"})


def is_known_kid(kid: str) -> bool:
    """Return True if `kid` is in the canonical whitelist."""
    return kid in KNOWN_KIDS


__all__ = ["KNOWN_KIDS", "is_known_kid"]
