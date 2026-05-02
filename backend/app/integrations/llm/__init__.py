"""Haiku-augmented LLM integrations.

Each module in this package is a thin wrapper around Claude Haiku that:
- Has a deterministic fallback path (graceful degradation)
- Caches results by content-hash (idempotent, cheap on repeat)
- Tracks cost-per-call when callers care
- Stays under 400 lines
"""
