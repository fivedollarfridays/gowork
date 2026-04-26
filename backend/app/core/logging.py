"""Structured logging configuration.

Includes a centralized PII scrubber (T13.94) so any structlog event
that carries a known-PII key (``session_id``, ``email``, ``phone``,
etc.) gets hashed at emit time rather than relying on per-call-site
discipline. The scrubber runs BEFORE the renderer so the rendered
output never contains the raw value.
"""

import logging
import logging.config

import structlog

from app.core.config import get_settings
from app.modules.compliance._audit import hash_session_id

# Keys whose values are treated as PII. Each is replaced with
# ``<key>_hash`` carrying the SHA256 hex of the raw value. Extend this
# tuple — DO NOT add scrubbing logic at call sites — when new PII
# fields enter the log surface.
_PII_KEYS: tuple[str, ...] = (
    "session_id",
    "email",
    "to_email",
    "from_email",
    "phone",
    "actor_email",
)


def _scrub_pii(_logger, _method_name, event_dict):
    """Structlog processor: hash known-PII keys at the event level.

    - Falsy values (``None``, ``""``) are dropped (no fake hashes).
    - Already-hashed keys (``session_id_hash``) pass through untouched
      — the processor is idempotent.
    - Non-PII fields are not modified.
    """
    for key in _PII_KEYS:
        if key in event_dict:
            value = event_dict.pop(key)
            if value:
                event_dict[f"{key}_hash"] = hash_session_id(str(value))
    return event_dict


def configure_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "level": settings.log_level,
                "handlers": ["default"],
            },
        }
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            _scrub_pii,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
