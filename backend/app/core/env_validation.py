"""Boot-time environment-variable validator (T13.118).

Two contracts:

1. **Required-on-boot vars** — the bare minimum to serve requests.
   If any are missing or empty, ``validate_required_env()`` raises
   ``RuntimeError`` with the offending name. The app refuses to start.
2. **Optional-but-affects-behavior vars** — LLM keys, SendGrid,
   BrightData, etc. If missing, the app falls back to a degraded mode
   (mock LLM, no email send) and we log a single WARNING per var.

The validator reads from ``os.environ`` directly so that test fixtures
can monkeypatch the env without invalidating any cached settings.

Audit-trail safety: only var **names** are ever logged, never values.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Required-on-boot. The app refuses to start if any of these are
# missing or empty. Deliberately tight — every entry must be one we
# would consider a hard production blocker.
REQUIRED_BOOT_VARS: tuple[str, ...] = (
    "DATABASE_URL",
    "ADMIN_API_KEY",
    "AUDIT_HASH_SALT",
)

# Optional but behavior-affecting. Missing → degraded mode + warn.
# Order is mostly informational (groups by domain).
OPTIONAL_BEHAVIOR_VARS: tuple[str, ...] = (
    # LLM providers — at least one of these should be set in
    # production. With none set, the app falls back to the mock
    # provider (already an explicit fallback in app/ai/llm_client).
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    # Outbound email (T12.10a appointment reminders + T12.19 digest
    # delivery). Without these, FEATURE_EMAIL_SEND_ENABLED still gates
    # at the dispatcher layer; the app boots cleanly either way.
    "SENDGRID_API_KEY",
    "SENDGRID_FROM_EMAIL",
    # Token signers (T12.10b appointments, T12.36 compliance, T12.19
    # unsubscribe). Each module raises at signing time if its secret
    # is unset, but the app can still boot and serve read-only routes.
    "APPOINTMENT_TOKEN_SECRET",
    "COMPLIANCE_TOKEN_SECRET",
    "UNSUBSCRIBE_TOKEN_SECRET",
    # Live job-board crawl (BrightData S6/S7 work). Without it the
    # jobs panel falls back to the seeded/static job set.
    "BRIGHTDATA_API_KEY",
    "BRIGHTDATA_DATASET_ID",
    # CORS lockdown — has a localhost dev default but should be set
    # explicitly in any deployed env.
    "CORS_ORIGINS",
)


def _is_missing(value: str | None) -> bool:
    """Treat both unset and empty-string as missing."""
    return value is None or value.strip() == ""


def _check_required(missing: list[str]) -> None:
    """Raise ``RuntimeError`` naming every missing required var."""
    if not missing:
        return
    if len(missing) == 1:
        raise RuntimeError(
            f"Required environment variable {missing[0]} is not set. "
            f"The app cannot start. See .env.example for the full list."
        )
    raise RuntimeError(
        f"Required environment variables are not set: {', '.join(missing)}. "
        f"The app cannot start. See .env.example for the full list."
    )


def _warn_optional_missing(name: str) -> None:
    """Emit a single WARNING for an unset optional var (name only)."""
    logger.warning(
        "Optional environment variable %s is missing — degraded mode.",
        name,
    )


def validate_required_env() -> None:
    """Validate required + optional env vars at app startup.

    Raises:
        RuntimeError: If any required var is missing or empty.
    """
    missing_required = [
        name for name in REQUIRED_BOOT_VARS if _is_missing(os.environ.get(name))
    ]
    _check_required(missing_required)

    for name in OPTIONAL_BEHAVIOR_VARS:
        if _is_missing(os.environ.get(name)):
            _warn_optional_missing(name)
