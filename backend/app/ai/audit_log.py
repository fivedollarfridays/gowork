"""PII-safe audit logging for LLM interactions.

Writes one JSON object per line (JSONL) with hashed session IDs.
No user content is logged — only metadata (lengths, provider, latency).
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def hash_session_id(session_id: str, salt: str = "") -> str:
    """Hash a session ID with salted sha256 for PII-safe logging."""
    return hashlib.sha256((salt + session_id).encode()).hexdigest()


def _write_log_entry(log_path: str, entry: dict) -> None:
    """Synchronous file write for audit log entry."""
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        logger.warning("Failed to write audit log to %s", log_path, exc_info=True)


def log_llm_interaction(
    log_path: str,
    session_id: str,
    provider: str,
    prompt_length: int,
    response_length: int,
    latency_ms: float,
) -> None:
    """Append a JSONL audit entry (sync). Use log_llm_interaction_async on async paths."""
    if not log_path:
        return
    entry = _build_entry(session_id, provider, prompt_length, response_length, latency_ms)
    _write_log_entry(log_path, entry)


async def log_llm_interaction_async(
    log_path: str,
    session_id: str,
    provider: str,
    prompt_length: int,
    response_length: int,
    latency_ms: float,
) -> None:
    """Append a JSONL audit entry without blocking the event loop."""
    if not log_path:
        return
    entry = _build_entry(session_id, provider, prompt_length, response_length, latency_ms)
    await asyncio.to_thread(_write_log_entry, log_path, entry)


def _build_entry(
    session_id: str, provider: str,
    prompt_length: int, response_length: int, latency_ms: float,
) -> dict:
    from app.core.config import get_settings
    salt = get_settings().audit_hash_salt
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hashed_session": hash_session_id(session_id, salt),
        "provider": provider,
        "prompt_length": prompt_length,
        "response_length": response_length,
        "latency_ms": latency_ms,
    }
