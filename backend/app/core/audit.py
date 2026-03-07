"""Structured audit logging for sensitive operations."""

import json
import logging

_logger = logging.getLogger("audit")


def audit_log(event: str, *, session_id: str, client_ip: str, **details: object) -> None:
    """Emit a structured audit log entry as JSON."""
    entry = {"event": event, "session_id": session_id, "client_ip": client_ip, **details}
    _logger.info(json.dumps(entry, default=str))
