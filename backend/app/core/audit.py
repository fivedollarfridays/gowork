"""Structured audit logging for sensitive operations."""

import json
import logging

from starlette.requests import Request

_logger = logging.getLogger("audit")


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, falling back to 'unknown'."""
    return request.client.host if request.client else "unknown"


def audit_log(event: str, *, session_id: str, client_ip: str, **details: object) -> None:
    """Emit a structured audit log entry as JSON."""
    entry = {"event": event, "session_id": session_id, "client_ip": client_ip, **details}
    _logger.info(json.dumps(entry, default=str))
