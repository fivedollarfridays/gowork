"""Structured logging helpers for barrier intelligence requests."""


def build_request_log(
    session_hash: str,
    mode: str,
    root_barriers: list[str],
    retrieval_doc_count: int,
    retrieval_latency_ms: float,
    llm_latency_ms: float,
    input_tokens: int,
    output_chunks: int,
    cache_hit: bool,
    guardrail_triggered: bool,
) -> dict:
    """Build a structured log dict for a barrier intel request."""
    return {
        "session_hash": session_hash,
        "mode": mode,
        "root_barriers": root_barriers,
        "retrieval_doc_count": retrieval_doc_count,
        "retrieval_latency_ms": round(retrieval_latency_ms, 1),
        "llm_latency_ms": round(llm_latency_ms, 1),
        "input_tokens": input_tokens,
        "output_chunks": output_chunks,
        "cache_hit": cache_hit,
        "guardrail_triggered": guardrail_triggered,
    }
