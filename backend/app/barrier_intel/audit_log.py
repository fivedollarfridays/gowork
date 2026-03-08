"""PII-safe structured audit logger for barrier intelligence chat."""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_LOG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "logs" / "barrier_intel_audit.jsonl"
)


def _hash_session(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:12]


def write_audit_entry(
    session_id: str,
    mode: str,
    root_barriers: list[str],
    retrieval_doc_ids: list[str],
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    guardrail_triggered: bool,
    log_path: Path | None = None,
) -> None:
    """Append one PII-safe JSONL record to the audit log."""
    path = log_path or _DEFAULT_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_hash": _hash_session(session_id),
        "mode": mode,
        "root_barriers": root_barriers,
        "retrieval_doc_ids": retrieval_doc_ids,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": round(latency_ms, 1),
        "guardrail_triggered": guardrail_triggered,
    }
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as exc:
        logger.warning("Failed to write barrier intel audit log: %s", exc)
