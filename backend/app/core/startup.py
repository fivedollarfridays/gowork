"""Startup seed and initialization routines."""

import logging

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.barrier_graph.seed import upsert_barrier_graph
from app.core.cleanup import cleanup_expired_sessions
from app.integrations.honestjobs.seed import seed_honestjobs_listings
from app.modules.criminal.employer_seed import seed_employer_policies
from app.rag.store import RagStore

logger = logging.getLogger(__name__)


async def run_seeds_and_rag(factory: async_sessionmaker) -> RagStore:
    """Execute all seed operations and build RAG store."""
    async with factory() as session:
        deleted = await cleanup_expired_sessions(session)
        if deleted:
            logger.info("Startup cleanup: removed %d expired sessions", deleted)
    async with factory() as session:
        await upsert_barrier_graph(session)
        await seed_employer_policies(session)
    async with factory() as session:
        await seed_honestjobs_listings(session)
    rag_store = RagStore()
    async with factory() as session:
        await rag_store.build_or_load(session)
    return rag_store
