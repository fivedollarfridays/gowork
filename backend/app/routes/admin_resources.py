"""Admin resource CRUD routes (T26.2).

Six endpoints under ``/api/admin/resources/...``, all gated by
:func:`require_role("admin")` (S22 cookie pattern):

* ``GET    /api/admin/resources?city=&limit=&offset=&include_hidden=``
* ``GET    /api/admin/resources/{id}``
* ``POST   /api/admin/resources`` (returns ``{id, ...}``)
* ``PATCH  /api/admin/resources/{id}``
* ``DELETE /api/admin/resources/{id}`` (soft-hide via set_health_status)
* ``POST   /api/admin/resources/{id}/restore`` (sets health_status='healthy')

Every write path stamps ``resources.user_curated_at = now()``, consuming
T26.1's loader-respect contract: rows the admin curates here are not
overwritten by the seed loader on container restart.

This module is *additive*: it ships in a new file rather than extending
``routes/admin_feedback.py`` because the feedback surface is scoped to
flagged-queue + visit-inbox actions; mixing CRUD into that file would
muddy the trust+audit story (different audit table contracts).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_admin_resources
from app.core.auth_roles import require_role
from app.core.database import get_db


router = APIRouter(prefix="/api/admin/resources", tags=["admin", "resources"])

_require_admin = require_role("admin")


class CreateResourceBody(BaseModel):
    """POST /api/admin/resources body.

    Required: ``name``, ``category``, ``city``. Optional fields mirror
    the writable subset of ``resources`` columns; ``health_status`` is
    forced to ``'healthy'`` server-side and ``user_curated_at`` is
    stamped server-side — neither is client-supplied.
    """

    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=80)
    city: str = Field(min_length=1, max_length=80)
    subcategory: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    phone: str | None = None
    url: str | None = None
    eligibility: str | None = None
    services: str | None = None
    hours: str | None = None
    notes: str | None = None
    barrier_affinity: str | None = None


class UpdateResourcePatch(BaseModel):
    """PATCH /api/admin/resources/{id} body — partial update.

    Every field is optional; the route stamps ``user_curated_at`` even
    when no other field changed (touch-as-curation semantics).
    """

    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    city: str | None = Field(default=None, min_length=1, max_length=80)
    subcategory: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    phone: str | None = None
    url: str | None = None
    eligibility: str | None = None
    services: str | None = None
    hours: str | None = None
    notes: str | None = None
    barrier_affinity: str | None = None


@router.get("")
async def list_resources(
    city: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_hidden: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Paginated browse of resources.

    Default page size 50; FastAPI clamps ``limit`` at 100 (returns 422
    above that). ``include_hidden=true`` opts soft-deleted rows back in;
    ``city=<slug>`` scopes to one city. Response echoes ``limit`` +
    ``offset`` + ``total`` so the UI can render "showing N–M of total".
    """
    rows, total = await queries_admin_resources.list_resources(
        db, city=city, limit=limit, offset=offset,
        include_hidden=include_hidden,
    )
    return {
        "items": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{resource_id}")
async def get_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Return a single resource by id, or 404 when absent."""
    row = await queries_admin_resources.get_resource(db, resource_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return row


@router.post("", status_code=201)
async def create_resource(
    body: CreateResourceBody,
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Create a new resource. Stamps ``user_curated_at = now()``.

    Returns the full created row (including the new ``id``) so the UI
    can update its table without a follow-up GET.
    """
    fields = body.model_dump(exclude_none=True)
    new_id = await queries_admin_resources.create_resource(db, **fields)
    created = await queries_admin_resources.get_resource(db, new_id)
    if created is None:
        # Defensive: created in this transaction, must exist on read-back.
        raise HTTPException(
            status_code=500, detail="Resource not retrievable after create"
        )
    return created


@router.patch("/{resource_id}")
async def update_resource(
    resource_id: int,
    patch: UpdateResourcePatch,
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Patch a resource. Stamps ``user_curated_at = now()`` on every call.

    404 when *resource_id* does not exist. Returns the full updated row.
    """
    fields = patch.model_dump(exclude_none=True)
    matched = await queries_admin_resources.update_resource(
        db, resource_id, **fields
    )
    if not matched:
        raise HTTPException(status_code=404, detail="Resource not found")
    updated = await queries_admin_resources.get_resource(db, resource_id)
    if updated is None:
        raise HTTPException(
            status_code=500, detail="Resource not retrievable after update"
        )
    return updated


@router.delete("/{resource_id}", status_code=204)
async def hide_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> Response:
    """Soft-delete: set ``health_status='hidden'``.

    The row stays in the table so audit trails (feedback rows that
    reference it) remain intact. Use POST /restore to reverse. 204 on
    success; 404 when *resource_id* does not exist.
    """
    matched = await queries_admin_resources.set_health_status(
        db, resource_id, "hidden"
    )
    if not matched:
        raise HTTPException(status_code=404, detail="Resource not found")
    return Response(status_code=204)


@router.post("/{resource_id}/restore")
async def restore_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Reverse a soft-delete: set ``health_status='healthy'``.

    Returns the new ``health_status`` for echoing back to the UI.
    404 when *resource_id* does not exist.
    """
    matched = await queries_admin_resources.set_health_status(
        db, resource_id, "healthy"
    )
    if not matched:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"id": resource_id, "health_status": "healthy"}


__all__ = ["router", "CreateResourceBody", "UpdateResourcePatch"]
