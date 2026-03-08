"""PII-safe audit logging for LLM interactions.

Writes one JSON object per line (JSONL) with hashed session IDs.
No user content is logged — only metadata (lengths, provider, latency).
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def hash_session_id(session_id: str) -> str:
    """Hash a session ID with sha256 for PII-safe logging."""
    return hashlib.sha256(session_id.encode()).hexdigest()


def log_llm_interaction(
    log_path: str,
    session_id: str,
    provider: str,
    prompt_length: int,
    response_length: int,
    latency_ms: float,
) -> None:
    """Append a JSONL audit entry for an LLM interaction.

    Args:
        log_path: File path for the JSONL log. Skips if empty.
        session_id: Raw session ID (will be hashed before writing).
        provider: LLM provider name (anthropic, openai, gemini, mock).
        prompt_length: Character count of the prompt (not the content).
        response_length: Character count of the response (not the content).
        latency_ms: Round-trip latency in milliseconds.
    """
    if not log_path:
        return

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hashed_session": hash_session_id(session_id),
        "provider": provider,
        "prompt_length": prompt_length,
        "response_length": response_length,
        "latency_ms": latency_ms,
    }

    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        logger.warning("Failed to write audit log to %s", log_path, exc_info=True)
