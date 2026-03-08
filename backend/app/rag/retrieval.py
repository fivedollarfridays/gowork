"""Hybrid retrieval layer — assembles RetrievalContext for barrier-intel chat."""

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.barrier_graph.queries import get_top_resources_for_barriers
from app.barrier_graph.traversal import find_root_barriers
from app.rag.document_schema import RetrievalContext
from app.rag.store import RagStore


def _build_enriched_query(
    barrier_ids: list[str],
    user_zip: str,
    user_schedule: str | None,
) -> str:
    barriers_str = ", ".join(barrier_ids) if barrier_ids else "general employment"
    schedule_str = user_schedule or "flexible"
    return (
        f"User in ZIP {user_zip} with barriers: {barriers_str}. "
        f"Work schedule: {schedule_str}. "
        f"What resources and steps help overcome these barriers?"
    )


def _build_chain_summary(root_barriers: list[dict], all_ids: list[str]) -> str:
    """Build readable chain summary from root barriers → downstream."""
    if not root_barriers:
        return "No barriers identified"
    root_names = [b.get("name") or b["id"].replace("_", " ").title()
                  for b in root_barriers]
    non_roots = [bid for bid in all_ids
                 if bid not in {b["id"] for b in root_barriers}]
    if not non_roots:
        return " → ".join(root_names)
    downstream = [bid.replace("_", " ").title() for bid in non_roots[:2]]
    return " → ".join(root_names + downstream)


async def retrieve_context(
    barrier_ids: list[str],
    user_zip: str,
    user_schedule: str | None,
    db: AsyncSession,
    store: RagStore,
    k: int = 8,
    top_n_resources: int = 5,
) -> RetrievalContext:
    """Assemble a full RetrievalContext for the given session."""
    t0 = time.monotonic()

    root_barriers = await find_root_barriers(barrier_ids, db)
    root_ids = [b["id"] for b in root_barriers] or barrier_ids

    top_resources = await get_top_resources_for_barriers(db, root_ids, n=top_n_resources)

    query = _build_enriched_query(barrier_ids, user_zip, user_schedule)
    retrieved_docs = store.search(query, barrier_filter=root_ids or None, k=k)

    latency_ms = (time.monotonic() - t0) * 1000
    chain_summary = _build_chain_summary(root_barriers, barrier_ids)

    return RetrievalContext(
        root_barriers=root_ids,
        barrier_chain_summary=chain_summary,
        top_resources=top_resources,
        retrieved_docs=retrieved_docs,
        user_zip=user_zip,
        user_schedule=user_schedule,
        retrieval_latency_ms=latency_ms,
    )
