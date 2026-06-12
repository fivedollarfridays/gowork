"""Async query helpers for the admin feedback surfaces (T26.3).

Two read surfaces + three mutations:

* :func:`list_flagged_resources` — resources at ``health_status='flagged'``
  joined with their last-30-days negative ``resource_feedback`` rows for
  context. Optional city filter via the ``city`` column added in m008.
* :func:`set_resource_health` — write-side helper used by approve /
  confirm-hide; mirrors the contract T26.2's CRUD writer will share but
  scoped here to the two transitions this sprint exposes.
* :func:`list_visit_feedback` — paginated browse of ``visit_feedback``
  with optional ``reviewed`` filter; returns (rows, total) so the route
  can echo offset + total without a second roundtrip.
* :func:`mark_visit_feedback_reviewed` — sets ``reviewed=1`` and
  optionally stamps ``action_taken``.

Every query uses :func:`sqlalchemy.text` + named binds so the module is
portable across the sqlite + postgres axes T22.2 / T23.9 stood up.
``RETURNING`` is used on the mutation paths so existence checks don't
require a second SELECT.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession


_NEGATIVE_FEEDBACK_WINDOW_DAYS = 30


async def _fetch_recent_negative_feedback(
    db: AsyncSession, resource_ids: list[int]
) -> dict[int, list[dict[str, Any]]]:
    """Bulk-load last-30d negative feedback grouped by resource_id.

    Returns a dict so the caller can attach a list to each flagged-row
    in one pass without an N+1. Empty dict on empty input.
    """
    if not resource_ids:
        return {}
    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=_NEGATIVE_FEEDBACK_WINDOW_DAYS)
    ).isoformat()
    # ``expanding=True`` is the driver-agnostic IN-clause shape
    # SQLAlchemy supports on both sqlite and postgres.
    stmt = text(
        "SELECT resource_id, session_id, barrier_type, submitted_at "
        "FROM resource_feedback "
        "WHERE helpful = 0 "
        "  AND submitted_at > :cutoff "
        "  AND resource_id IN :rids "
        "ORDER BY submitted_at DESC"
    ).bindparams(bindparam("rids", expanding=True))
    result = await db.execute(
        stmt, {"cutoff": cutoff, "rids": list(resource_ids)},
    )
    grouped: dict[int, list[dict[str, Any]]] = {rid: [] for rid in resource_ids}
    for row in result:
        m = row._mapping
        grouped[int(m["resource_id"])].append({
            "session_id": m["session_id"],
            "barrier_type": m["barrier_type"],
            "submitted_at": m["submitted_at"],
        })
    return grouped


async def list_flagged_resources(
    db: AsyncSession, *, city: str | None = None
) -> list[dict[str, Any]]:
    """Return flagged resources with recent-negative-feedback context.

    Each row carries the resource's identifying columns plus a
    ``recent_negative_feedback`` list (newest-first) of negative
    feedback submitted in the last 30 days. Empty list when none.
    """
    sql = (
        "SELECT id, name, category, city, health_status, address, "
        "phone, url "
        "FROM resources "
        "WHERE health_status = 'flagged'"
    )
    binds: dict[str, Any] = {}
    if city is not None:
        sql += " AND city = :city"
        binds["city"] = city
    sql += " ORDER BY id ASC"

    result = await db.execute(text(sql), binds)
    rows = [dict(r._mapping) for r in result]
    if not rows:
        return []

    fb = await _fetch_recent_negative_feedback(
        db, [int(r["id"]) for r in rows]
    )
    for row in rows:
        row["recent_negative_feedback"] = fb.get(int(row["id"]), [])
    return rows


async def set_resource_health(
    db: AsyncSession, resource_id: int, status: str
) -> bool:
    """Update ``resources.health_status`` for *resource_id*.

    Returns ``True`` if a row was updated, ``False`` when no row
    matched. Caller is responsible for the route-level 404 surface.
    Uses ``RETURNING id`` so existence is detected in a single
    statement on both engines.
    """
    result = await db.execute(
        text(
            "UPDATE resources SET health_status = :status "
            "WHERE id = :rid RETURNING id"
        ),
        {"status": status, "rid": resource_id},
    )
    updated = result.first() is not None
    await db.commit()
    return updated


async def list_visit_feedback(
    db: AsyncSession,
    *,
    reviewed: bool | None,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    """Return (rows, total_count) for the visit-feedback inbox.

    ``reviewed`` filter:
      * ``None`` — all rows.
      * ``True`` — only rows with ``reviewed = 1``.
      * ``False`` — only rows with ``reviewed = 0``.

    Rows are sorted newest-first by ``submitted_at DESC`` so the
    inbox surfaces freshly-arrived feedback at the top.
    """
    where_clause = ""
    binds: dict[str, Any] = {"limit": limit, "offset": offset}
    if reviewed is not None:
        where_clause = "WHERE reviewed = :reviewed"
        binds["reviewed"] = 1 if reviewed else 0

    rows_sql = (
        "SELECT id, session_id, submitted_at, made_it_to_center, "
        "outcomes, plan_accuracy, free_text, reviewed, action_taken "
        f"FROM visit_feedback {where_clause} "
        "ORDER BY submitted_at DESC, id DESC "
        "LIMIT :limit OFFSET :offset"
    )
    rows_result = await db.execute(text(rows_sql), binds)
    rows = [dict(r._mapping) for r in rows_result]

    count_sql = f"SELECT COUNT(*) FROM visit_feedback {where_clause}"
    count_binds = {k: v for k, v in binds.items() if k not in {"limit", "offset"}}
    count_result = await db.execute(text(count_sql), count_binds)
    total = int(count_result.scalar_one() or 0)
    return rows, total


async def mark_visit_feedback_reviewed(
    db: AsyncSession,
    visit_id: int,
    action_taken: str | None,
) -> dict[str, Any] | None:
    """Flip ``reviewed=1`` on *visit_id* and stamp ``action_taken``.

    Returns ``{"id", "reviewed", "action_taken"}`` of the updated row,
    or ``None`` when no row matched (caller raises 404). ``RETURNING``
    keeps the existence check + payload in one statement.
    """
    result = await db.execute(
        text(
            "UPDATE visit_feedback "
            "SET reviewed = 1, action_taken = :action "
            "WHERE id = :vid "
            "RETURNING id, reviewed, action_taken"
        ),
        {"action": action_taken, "vid": visit_id},
    )
    row = result.first()
    if row is None:
        await db.commit()
        return None
    await db.commit()
    m = row._mapping
    return {
        "id": int(m["id"]),
        "reviewed": int(m["reviewed"]) == 1,
        "action_taken": m["action_taken"],
    }


__all__ = [
    "list_flagged_resources",
    "set_resource_health",
    "list_visit_feedback",
    "mark_visit_feedback_reviewed",
]
