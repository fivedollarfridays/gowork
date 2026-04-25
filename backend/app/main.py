"""MontGoWork API — Workforce Navigator (city-aware)."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.cities.config import get_city_config
from app.core.config import get_settings
from app.core.database import close_db, get_async_session_factory, get_engine, init_db
from app.core.exception_handlers import register_exception_handlers
from app.core.lifespan_helpers import (
    log_startup_warnings,
    register_db_listeners,
    start_scheduler_with_guard,
    stop_scheduler,
)
from app.routes import all_routers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Lazy imports avoid circular import + keep import count low.
    # T13.118: env validation runs BEFORE any downstream code can
    # silently default to a placeholder.
    from app.core.logging import configure_logging
    from app.core.env_validation import validate_required_env
    from app.core.startup import run_seeds_and_rag

    configure_logging()
    logger.info("MontGoWork API starting up")
    validate_required_env()
    get_settings()

    llm_status = log_startup_warnings()
    engine = get_engine()
    await init_db(engine)
    register_db_listeners(settings.database_url)
    factory = get_async_session_factory()
    app.state.rag_store = await run_seeds_and_rag(factory)
    app.state.llm_status = llm_status
    # APScheduler: single-worker hard constraint + lifecycle.
    # Multi-worker safety via scheduler_leases is deferred (T12.3).
    start_scheduler_with_guard()
    try:
        yield
    finally:
        stop_scheduler()
        await close_db()
        logger.info("MontGoWork API shutting down")


settings = get_settings()
_is_production = settings.environment == "production"

_city = get_city_config()
_api_desc = f"Workforce Navigator for {_city.location}"

app = FastAPI(
    title="MontGoWork API",
    description=_api_desc,
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
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

_trusted = [h.strip() for h in settings.trusted_proxy_hosts.split(",") if h.strip()]
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=_trusted)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Set security headers on all responses (LOW-6, S-M4)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if _is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

for _router in all_routers:
    app.include_router(_router)


@app.get("/")
async def root() -> dict:
    return {"message": "MontGoWork API", "status": "running"}
