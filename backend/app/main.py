"""MontGoWork API — Workforce Navigator for Montgomery, Alabama"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import get_settings
from app.barrier_graph.seed import upsert_barrier_graph
from app.core.database import close_db, get_async_session_factory, get_engine, init_db
from app.core.exception_handlers import register_exception_handlers
from app.rag.store import init_rag_store
from app.routes import all_routers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    from app.core.logging import configure_logging
    configure_logging()
    logger.info("MontGoWork API starting up")
    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY is not set — AI narrative will use fallback")
    web_concurrency = os.environ.get("WEB_CONCURRENCY", "1")
    if web_concurrency.isdigit() and int(web_concurrency) > 1:
        logger.warning(
            "WEB_CONCURRENCY=%s — rate limiting is per-process and will not "
            "be shared across workers. Consider using Redis-backed rate limit "
            "or running a single worker.",
            web_concurrency,
        )
    engine = get_engine()
    await init_db(engine)
    factory = get_async_session_factory()
    async with factory() as session:
        await upsert_barrier_graph(session)
    async with factory() as session:
        await init_rag_store(session)
    yield
    await close_db()
    logger.info("MontGoWork API shutting down")


settings = get_settings()
_is_production = settings.environment == "production"

app = FastAPI(
    title="MontGoWork API",
    description="Workforce Navigator for Montgomery, Alabama",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

_trusted = [h.strip() for h in settings.trusted_proxy_hosts.split(",") if h.strip()]
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=_trusted)

for _router in all_routers:
    app.include_router(_router)


@app.get("/")
async def root():
    return {"message": "MontGoWork API", "status": "running"}
