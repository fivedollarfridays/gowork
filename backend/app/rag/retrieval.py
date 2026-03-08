"""Hybrid retrieval layer: graph + vector search + context assembly."""

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.barrier_graph.queries import get_top_resources_for_barriers
from app.barrier_graph.traversal import find_root_barriers
from app.rag.document_schema import RetrievalContext
from app.rag.store import RagStore


def build_enriched_query(
    barrier_codes: list[str],
    zip_code: str | None = None,
    schedule: str | None = None,
) -> str:
    """Build a search query enriched with user context."""
    parts = [f"User with barriers: {', '.join(barrier_codes)}."]
    if zip_code:
        parts.append(f"Located in ZIP {zip_code}.")
    if schedule:
        parts.append(f"Work schedule: {schedule}.")
    parts.append("What resources and steps help overcome these barriers?")
    return " ".join(parts)


def _build_chain_summary(root_barriers: list[dict], all_codes: list[str]) -> str:
    """Build a readable barrier chain summary."""
    root_names = [b["name"] for b in root_barriers]
    non_root = [c for c in all_codes if c not in {b["id"] for b in root_barriers}]
    if not non_root:
        return " → ".join(root_names) if root_names else ""
    return " → ".join(root_names) + " → " + ", ".join(non_root)


async def retrieve_context(
    barrier_codes: list[str],
    db_session: AsyncSession,
    store: RagStore,
    zip_code: str | None = None,
    schedule: str | None = None,
) -> RetrievalContext:
    """Assemble full retrieval context from graph + vector search."""
    start = time.monotonic()

    root_barriers = await find_root_barriers(barrier_codes, db_session)
    root_ids = [b["id"] for b in root_barriers]

    top_resources = await get_top_resources_for_barriers(
        db_session, root_ids, n=5
    )

    query = build_enriched_query(barrier_codes, zip_code, schedule)
    retrieved_docs = store.search(query, barrier_filter=root_ids, n=8)

    chain_summary = _build_chain_summary(root_barriers, barrier_codes)
    latency_ms = (time.monotonic() - start) * 1000

    return RetrievalContext(
        root_barriers=root_barriers,
        barrier_chain_summary=chain_summary,
        top_resources=top_resources,
        retrieved_docs=retrieved_docs,
        user_zip=zip_code,
        user_schedule=schedule,
        retrieval_latency_ms=latency_ms,
    )
