"""MontGoWork API — Workforce Navigator for Montgomery, Alabama"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import close_db, get_engine, init_db
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.health import router as health_router
from app.routes.assessment import router as assessment_router
from app.routes.brightdata import router as brightdata_router
from app.routes.credit import router as credit_router
from app.routes.feedback import router as feedback_router
from app.routes.jobs import router as jobs_router
from app.routes.plan import router as plan_router

logger = logging.getLogger(__name__)

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    logger.info("MontGoWork API starting up")
    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY is not set — AI narrative will use fallback")
    engine = get_engine()
    await init_db(engine)
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

app.include_router(health_router)
app.include_router(assessment_router)
app.include_router(plan_router)
app.include_router(credit_router)
app.include_router(jobs_router)
app.include_router(brightdata_router)
app.include_router(feedback_router)


@app.get("/")
async def root():
    return {"message": "MontGoWork API", "status": "running"}
