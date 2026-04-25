"""Helpers extracted from `app.main` to keep that module's import
count manageable (T13.118).

These functions are called from `app.main.lifespan`. They're factored
out so the FastAPI entry-point file stays focused on app composition.
"""

from __future__ import annotations

import logging
import os

from app.ai.llm_client import check_llm_providers
from app.core.scheduler import (
    enforce_single_worker,
    scheduler_state_summary,
    shutdown_scheduler,
    start_scheduler,
)
from app.modules.appointments.outcomes_listener import register_outcomes_listener

logger = logging.getLogger("app.main")


def log_startup_warnings() -> dict:
    """Log startup warnings + return LLM provider status."""
    if not os.environ.get("ENVIRONMENT"):
        logger.warning(
            "ENVIRONMENT not set — defaulting to 'development'. "
            "Set ENVIRONMENT explicitly for production deployments."
        )
    llm_status = check_llm_providers()
    logger.info(
        "LLM providers: %s (active: %s)",
        llm_status["providers"],
        llm_status["active"],
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


def register_db_listeners(database_url: str) -> None:
    """Wire SQLAlchemy event listeners that depend on the live DB URL."""
    register_outcomes_listener(database_url.split(":///", 1)[-1])


def start_scheduler_with_guard() -> None:
    """Enforce single-worker constraint, then start APScheduler."""
    enforce_single_worker()
    start_scheduler()
    logger.info(scheduler_state_summary())


def stop_scheduler() -> None:
    """Tear down APScheduler. Mirrors `start_scheduler_with_guard`."""
    shutdown_scheduler(wait=False)
