"""Async query helpers for the admin resource CRUD surface (T26.2).

Five helpers backing the six routes mounted under
``/api/admin/resources/...``:

* :func:`list_resources` — paginated list filtered by city; default
  excludes ``health_status='hidden'`` rows. Returns ``(rows, total)``
  so the route can echo offset/total without a second roundtrip.
* :func:`get_resource` — single-row read; ``None`` when not found.
* :func:`create_resource` — INSERT + stamps ``user_curated_at = now()``.
  Returns the new ``id``. Consumes T26.1's loader-respect contract: any
  row this function inserts is preserved across container restarts
  because ``seed_from_file`` skips ``(city, name)`` pairs whose existing
  row carries ``user_curated_at IS NOT NULL``.
* :func:`update_resource` — UPDATE + stamps ``user_curated_at = now()``.
  Returns ``True`` if a row matched, ``False`` for 404 surfacing.
* :func:`set_health_status` — sole writer to ``resources.health_status``
  for the admin CRUD surface; allowed values are ``'healthy'``,
  ``'watch'``, ``'flagged'``, ``'hidden'``. Mirrors the contract that
  T26.3's :func:`queries_admin_feedback.set_resource_health` uses for
  the flagged-queue actions; same column, same allowed values, kept as
  separate functions so each surface owns its own audit story.

Every query uses :func:`sqlalchemy.text` + named binds so the module is
portable across the sqlite + postgres axes T22.2 / T23.9 stood up.
``RETURNING id`` keeps existence checks single-statement on both engines.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# Columns the admin CRUD surface is allowed to write. Mirrors the
# subset of ``schema.ALLOWED_COLUMNS["resources"]`` that the admin
# UI exposes — ``health_status`` is deliberately routed through
# :func:`set_health_status` (sole writer) and ``user_curated_at`` is
# stamped server-side, never client-supplied.
WRITABLE_COLUMNS: frozenset[str] = frozenset({
    "name", "category", "subcategory", "address", "lat", "lng",
    "phone", "url", "eligibility", "services", "hours", "notes",
    "city", "barrier_affinity",
})


ALLOWED_HEALTH_STATUSES: frozenset[str] = frozenset({
    "healthy", "watch", "flagged", "hidden",
})


_SELECT_COLUMNS = (
    "id, name, category, subcategory, address, lat, lng, phone, url, "
    "eligibility, services, hours, notes, city, barrier_affinity, "
    "health_status, user_curated_at"
)


def _now_iso() -> str:
    """UTC now as an ISO-8601 string — what the column stores on sqlite.

    Postgres accepts the same ISO string for a TIMESTAMP column, so this
    keeps the writes driver-agnostic without a CASE for ``func.now()``.
    """
    return datetime.now(timezone.utc).isoformat()


def _build_list_where(
    *, city: str | None, include_hidden: bool,
) -> tuple[str, dict[str, Any]]:
    """Compose the WHERE clause + filter binds for :func:`list_resources`.

    Returns ``("", {})`` when no filters apply. The returned binds
    cover only the filter columns; pagination binds are layered on
    by the caller.
    """
    where: list[str] = []
    binds: dict[str, Any] = {}
    if city is not None:
        where.append("city = :city")
        binds["city"] = city
    if not include_hidden:
        where.append("health_status != 'hidden'")
    where_clause = ("WHERE " + " AND ".join(where)) if where else ""
    return where_clause, binds


async def list_resources(
    db: AsyncSession,
    *,
    city: str | None,
    limit: int,
    offset: int,
    include_hidden: bool,
) -> tuple[list[dict[str, Any]], int]:
    """Return (rows, total_count) for the admin list surface.

    Filters:
      * ``city`` — when not ``None``, scope to that slug.
      * ``include_hidden`` — when ``False`` (default), exclude rows
        whose ``health_status='hidden'`` so soft-deleted entries
        don't clutter the default list.

    Rows ordered by ``id ASC`` for deterministic pagination across
    repeated requests with the same offset.
    """
    where_clause, filter_binds = _build_list_where(
        city=city, include_hidden=include_hidden,
    )
    rows_sql = (
        f"SELECT {_SELECT_COLUMNS} FROM resources {where_clause} "
        "ORDER BY id ASC LIMIT :limit OFFSET :offset"
    )
    rows_result = await db.execute(
        text(rows_sql),
        {**filter_binds, "limit": limit, "offset": offset},
    )
    rows = [dict(r._mapping) for r in rows_result]

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM resources {where_clause}"), filter_binds,
    )
    total = int(count_result.scalar_one() or 0)
    return rows, total


async def get_resource(
    db: AsyncSession, resource_id: int
) -> dict[str, Any] | None:
    """Return the resource row for *resource_id*, or ``None`` if absent."""
    result = await db.execute(
        text(
            f"SELECT {_SELECT_COLUMNS} FROM resources WHERE id = :id"
        ),
        {"id": resource_id},
    )
    row = result.first()
    return dict(row._mapping) if row is not None else None


def _filter_writable(fields: dict[str, Any]) -> dict[str, Any]:
    """Drop keys not in :data:`WRITABLE_COLUMNS` so a stray client field
    can't write to ``health_status`` or ``user_curated_at``."""
    return {k: v for k, v in fields.items() if k in WRITABLE_COLUMNS}


async def create_resource(
    db: AsyncSession, **fields: Any
) -> int:
    """INSERT a new resource row; stamp ``user_curated_at = now()``.

    Returns the new ``id``. Required minimums (``name`` + ``category``)
    are enforced at the route layer (Pydantic model); this function
    trusts its caller to have validated the shape.

    ``health_status`` is forced to ``'healthy'`` on create — admins
    don't typically file new rows in any other state, and routing
    every state transition through :func:`set_health_status` keeps
    the audit story uniform.
    """
    clean = _filter_writable(fields)
    # ``health_status`` is intentionally NOT in WRITABLE_COLUMNS so we
    # set it explicitly here. Same with the curation marker.
    clean["health_status"] = "healthy"
    clean["user_curated_at"] = _now_iso()

    columns = ", ".join(clean.keys())
    placeholders = ", ".join(f":{k}" for k in clean.keys())
    result = await db.execute(
        text(
            f"INSERT INTO resources ({columns}) "
            f"VALUES ({placeholders}) RETURNING id"
        ),
        clean,
    )
    new_id = int(result.scalar_one())
    await db.commit()
    return new_id


async def update_resource(
    db: AsyncSession, resource_id: int, **patch: Any
) -> bool:
    """UPDATE the patched fields; stamp ``user_curated_at = now()``.

    Returns ``True`` if a row matched, ``False`` for 404 surfacing.
    Empty-patch (no writable fields) still stamps the timestamp — the
    operator's "I touched this row" intent is recorded even when no
    field changed, which matches the loader-respect contract: a touched
    row is a curated row.
    """
    clean = _filter_writable(patch)
    clean["user_curated_at"] = _now_iso()

    set_clause = ", ".join(f"{col} = :{col}" for col in clean.keys())
    binds = dict(clean)
    binds["__rid"] = resource_id
    result = await db.execute(
        text(
            f"UPDATE resources SET {set_clause} "
            "WHERE id = :__rid RETURNING id"
        ),
        binds,
    )
    matched = result.first() is not None
    await db.commit()
    return matched


async def set_health_status(
    db: AsyncSession, resource_id: int, status: str
) -> bool:
    """Update ``resources.health_status`` for *resource_id*.

    ``status`` must be one of :data:`ALLOWED_HEALTH_STATUSES`; raises
    :class:`ValueError` otherwise. Returns ``True`` on a matched row,
    ``False`` for 404 surfacing. Sole writer to ``health_status`` for
    the admin CRUD surface.
    """
    if status not in ALLOWED_HEALTH_STATUSES:
        raise ValueError(
            f"Invalid health_status {status!r}; "
            f"allowed: {sorted(ALLOWED_HEALTH_STATUSES)}"
        )
    result = await db.execute(
        text(
            "UPDATE resources SET health_status = :status "
            "WHERE id = :rid RETURNING id"
        ),
        {"status": status, "rid": resource_id},
    )
    matched = result.first() is not None
    await db.commit()
    return matched


__all__ = [
    "ALLOWED_HEALTH_STATUSES",
    "WRITABLE_COLUMNS",
    "create_resource",
    "get_resource",
    "list_resources",
    "set_health_status",
    "update_resource",
]
