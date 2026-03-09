"""MontGoWork API — Workforce Navigator for Montgomery, Alabama"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.ai.llm_client import check_llm_providers
from app.core.config import get_settings
from app.core.database import close_db, get_async_session_factory, get_engine, init_db
from app.core.exception_handlers import register_exception_handlers
from app.routes import all_routers

logger = logging.getLogger(__name__)


def _log_startup_warnings() -> dict:
    """Log startup warnings and return LLM provider status."""
    if not os.environ.get("ENVIRONMENT"):
        logger.warning(
            "ENVIRONMENT not set — defaulting to 'development'. "
            "Set ENVIRONMENT explicitly for production deployments."
        )
    llm_status = check_llm_providers()
    logger.info(
        "LLM providers: %s (active: %s)",
        llm_status["providers"], llm_status["active"],
    )
    if llm_status["active"] == "mock":
        logger.warning("No LLM provider configured — using mock fallback")
    web_concurrency = os.environ.get("WEB_CONCURRENCY", "1")
    if web_concurrency.isdigit() and int(web_concurrency) > 1:
        logger.warning(
            "WEB_CONCURRENCY=%s — rate limiting is per-process and will not "
            "be shared across workers. Consider using Redis-backed rate limit "
            "or running a single worker.",
            web_concurrency,
        )
    return llm_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    from app.core.logging import configure_logging
    configure_logging()
    logger.info("MontGoWork API starting up")
    get_settings()
    from app.core.startup import run_seeds_and_rag

    llm_status = _log_startup_warnings()
    engine = get_engine()
    await init_db(engine)
    factory = get_async_session_factory()
    app.state.rag_store = await run_seeds_and_rag(factory)
    app.state.llm_status = llm_status
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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Set security headers on all responses (LOW-6)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

for _router in all_routers:
    app.include_router(_router)


@app.get("/")
async def root() -> dict:
    return {"message": "MontGoWork API", "status": "running"}
