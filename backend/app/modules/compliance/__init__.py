"""Compliance module (T12.36) — worker data export + right-to-delete.

Hub for the three compliance capabilities required for production GA:

* :mod:`export`  — build JSON + Markdown archive; sign 24h single-use URL.
* :mod:`delete`  — full cascade delete + selective tombstone delete.
* :mod:`retention` — nightly sweep of sessions past ``expires_at + 90d``.

Every caller-facing API writes a row to ``compliance_audit`` (m006) so
there is a durable record of every access / deletion event.
"""

from app.modules.compliance import delete, export, retention

__all__ = ["delete", "export", "retention"]
