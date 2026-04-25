"""Spy + stub helpers for ``test_orchestrator_full_run.py`` (T13.53).

Hoisted out of the test file so it stays under the project's 600-line
ceiling. Pure helpers — no fixtures live here, so the test file can
import what it needs without pytest plugin coupling.

Each ``_stub_*`` helper monkeypatches one orchestrator step to:
1. Append a ``(step_name, session_id)`` entry to the shared call log.
2. Return a deterministic stub matching the documented return shape.

The two-tuple recorder ``(call_log, stub_table)`` is shared across every
spy in one test so the test body can assert against ordering AND any
deeper per-call payload (city, kwargs, etc.) the stash captures.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest


def make_recorder() -> tuple[list[tuple[str, str]], dict[str, Any]]:
    """Return the shared ``(call_log, stub_table)`` recorder pair."""
    return [], {}


def install_full_spy_set(
    monkeypatch: pytest.MonkeyPatch,
    *,
    compose_raises_for: str | None = None,
    refresh_raises_for: str | None = None,
) -> tuple[list[tuple[str, str]], dict[str, Any]]:
    """Monkeypatch every orchestrator step to record + stub its return.

    ``compose_raises_for`` and ``refresh_raises_for`` let one test verify
    the partial-failure contract by injecting a raise into a single
    session's branch without touching the others.
    """
    log, stash = make_recorder()
    stash.setdefault("compose_calls", [])
    stash.setdefault("send_calls", [])
    stash.setdefault("retention_calls", 0)
    stash.setdefault("weekly_calls", [])

    import scripts.nightly_digest as nd
    from scripts import _nightly_weekly

    _stub_pre_compose(
        monkeypatch, nd, log, refresh_raises_for=refresh_raises_for,
    )
    _stub_compose(monkeypatch, nd, log, stash, compose_raises_for)
    _stub_send_digest(monkeypatch, nd, log, stash)
    _stub_weekly_review(monkeypatch, _nightly_weekly, log, stash)
    _stub_retention(monkeypatch, nd, stash)
    return log, stash


def _stub_pre_compose(
    monkeypatch: pytest.MonkeyPatch,
    nd: Any,
    log: list[tuple[str, str]],
    *,
    refresh_raises_for: str | None,
) -> None:
    """Spy + stub the retro / reconcile / refresh trio in one helper.

    The orchestrator imports ``reconcile_session_appointments`` as a
    top-level name (``from ... import ...``), so we have to rebind it
    on the orchestrator module itself rather than on the source module.
    """
    from app.modules.plan.daily_progress import RetroResult
    from app.modules.plan.plan_refresher import RefreshResult

    def _retro(session_id: str, for_date: date, *, db_path: Any) -> RetroResult:
        log.append(("retro", session_id))
        return RetroResult(
            session_id=session_id, for_date=for_date,
            actions=[], completion_ratio=0.0, summary="stub",
        )

    def _reconcile(session_id: str, *, db_path: Any, now: Any = None) -> dict:
        log.append(("reconcile", session_id))
        return {"advanced": []}

    def _refresh(
        session_id: str, *, db_path: Any, now: Any = None,
        trigger_reason: Any = None,
    ) -> RefreshResult:
        log.append(("refresh", session_id))
        if refresh_raises_for is not None and session_id == refresh_raises_for:
            raise RuntimeError(f"refresh blew up for {session_id}")
        return RefreshResult(refreshed=False)

    monkeypatch.setattr(nd, "run_nightly_retro", _retro)
    monkeypatch.setattr(nd, "reconcile_session_appointments", _reconcile)
    monkeypatch.setattr(nd, "refresh_plan", _refresh)


def _stub_compose(
    monkeypatch: pytest.MonkeyPatch,
    nd: Any,
    log: list[tuple[str, str]],
    stash: dict[str, Any],
    raises_for: str | None,
) -> None:
    """Replace ``compose_digest`` with a recorder that stubs the output."""
    from app.modules.engagement.digest_composer import DigestResult
    from app.modules.common.temporal_types import ModuleStatus

    def _compose(
        session_id: str, for_date: date, *,
        db_path: Any, city: str | None = None, now: Any = None,
    ) -> DigestResult:
        log.append(("compose", session_id))
        stash["compose_calls"].append({
            "session_id": session_id,
            "city": city, "for_date": for_date,
        })
        if raises_for is not None and session_id == raises_for:
            raise RuntimeError(f"compose blew up for {session_id}")
        sentinel = ModuleStatus(
            module_name="resume_builder", health="healthy",
            signals={}, last_activity_at=None,
        )
        return DigestResult(
            subject=f"digest-{session_id}",
            html="<p>stub</p>", text="stub",
            section_counts={"yesterday": 0, "today": 0, "week": 0, "stall": 0},
            module_status=[sentinel],
        )

    monkeypatch.setattr(nd, "compose_digest", _compose)


def _stub_send_digest(
    monkeypatch: pytest.MonkeyPatch,
    nd: Any,
    log: list[tuple[str, str]],
    stash: dict[str, Any],
) -> None:
    """Replace ``send_digest`` with a recorder that returns a success."""
    from app.modules.engagement.reminder_engine import ReminderDispatchResult

    def _send(
        session_id: str, to_email: str, subject: str, html: str, text: str,
        *, db_path: Any = None, now: Any = None,
    ) -> ReminderDispatchResult:
        log.append(("send_digest", session_id))
        stash["send_calls"].append({
            "session_id": session_id, "to": to_email, "subject": subject,
        })
        return ReminderDispatchResult(
            success=True, skipped_reason=None,
            category="digest", message_id=f"mid-{session_id}",
        )

    monkeypatch.setattr(nd, "send_digest", _send)


def _stub_weekly_review(
    monkeypatch: pytest.MonkeyPatch,
    weekly_mod: Any,
    log: list[tuple[str, str]],
    stash: dict[str, Any],
) -> None:
    """Replace the Sunday-only ``send_weekly_review`` spoke with a recorder."""

    def _weekly(
        session_id: str, email: str, for_date: date, *,
        db_path: Any, send_fn: Any,
    ) -> None:
        log.append(("weekly_review", session_id))
        stash["weekly_calls"].append({
            "session_id": session_id, "email": email,
            "for_date": for_date,
        })

    monkeypatch.setattr(weekly_mod, "send_weekly_review", _weekly)


def _stub_retention(
    monkeypatch: pytest.MonkeyPatch,
    nd: Any,
    stash: dict[str, Any],
) -> None:
    """Replace ``retention_sweep`` so we can verify it fires once per run.

    The orchestrator imports the module as ``_retention_mod`` and invokes
    ``_retention_mod.retention_sweep``; patching the same attr on that
    module is the only path that intercepts the call.
    """

    def _sweep(*, db_path: Any, now: Any = None) -> list[str]:
        stash["retention_calls"] += 1
        return []

    monkeypatch.setattr(nd._retention_mod, "retention_sweep", _sweep)


__all__ = ["install_full_spy_set", "make_recorder"]
