"""Aggregate the four per-module ``nightly_status`` calls (T12.25b).

Ported from ``ops/lib/module_status_contract.py:discover_module_statuses``.
One function — :func:`collect_all` — invokes each module's
``nightly_status(session_id, *, db_path, now)`` and collects the results
into a deterministic list. A failing module surfaces a sentinel
``ModuleStatus`` with ``health='unknown'`` and an ``error`` signal; the
collector never raises on a single module's failure.

The aggregate list is consumed by:

* :mod:`app.modules.engagement.digest_composer` — attached to
  :class:`DigestResult.module_status` for observability.
* :mod:`app.routes.advisor_inbox` (T12.31) — prioritisation signals.

Both consumers pull the already-typed :class:`ModuleStatus` models; the
collector is the only place the import order is fixed so a wire-protocol
change (new module) is a single-file edit.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

from app.modules.common.temporal_types import ModuleStatus
from app.modules.documents import cover_letter_builder, resume_builder
from app.modules.engagement import reminder_engine
from app.modules.jobs import applications

logger = logging.getLogger(__name__)

# Ordered tuple: (module_name_for_sentinel, module). The name MUST match
# the value returned by the live implementation so downstream consumers
# can key by name either way. The collector resolves ``nightly_status``
# via ``getattr`` at call time (not import time) so monkeypatches and
# test shims are respected — matches the ops ``discover_module_statuses``
# pattern.
_MODULES: tuple[tuple[str, ModuleType], ...] = (
    ("resume_builder", resume_builder),
    ("cover_letter_builder", cover_letter_builder),
    ("applications", applications),
    ("reminder_engine", reminder_engine),
)


def collect_all(
    session_id: str, *, db_path: str | Path, now: datetime | None = None,
) -> list[ModuleStatus]:
    """Invoke each module's ``nightly_status`` and return the list.

    Order matches :data:`_MODULES`. A raising module is surfaced as a
    ``health='unknown'`` sentinel with an ``error`` signal rather than
    propagating the exception — mirrors the ops contract.
    """
    results: list[ModuleStatus] = []
    for module_name, module in _MODULES:
        results.append(
            _safe_call(module, module_name, session_id, db_path, now),
        )
    return results


def _safe_call(
    module: ModuleType,
    module_name: str,
    session_id: str,
    db_path: str | Path,
    now: datetime | None,
) -> ModuleStatus:
    """Resolve + call one module's ``nightly_status``; sentinel on failure."""
    try:
        fn = getattr(module, "nightly_status")
        return fn(session_id, db_path=db_path, now=now)
    except Exception as exc:  # noqa: BLE001 — deliberately broad; ops parity
        logger.exception(
            "status_collector: %s.nightly_status raised — sentinel emitted",
            module_name,
        )
        signals: dict[str, Any] = {"error": str(exc)}
        return ModuleStatus(
            module_name=module_name,
            health="unknown", signals=signals, last_activity_at=None,
        )


__all__ = ["collect_all"]
