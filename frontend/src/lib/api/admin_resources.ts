/**
 * Typed API client for the admin resource CRUD surface (T26.5).
 *
 * Six endpoints under ``/api/admin/resources``, all gated by
 * ``require_role("admin")`` on the backend (S22 cookie pattern). Mirrors
 * the S25 :file:`cities_admin.ts` shape post-/reviewing-and-fixing
 * lift: every function delegates transport to :func:`fetchWithCookie`
 * (which bakes in ``credentials: "include"``) and error-shaping to
 * :func:`throwOnApiError` from `_client.ts` — one typed error class
 * per domain, never a per-domain copy of the timeout/cookie wrapper.
 *
 * Wire types match the backend dict shape returned by
 * :mod:`app.core.queries_admin_resources` 1:1, including the
 * server-stamped ``user_curated_at`` (T26.1's loader-respect contract:
 * any row with this column populated survives the seed loader).
 */

import { fetchWithCookie, throwOnApiError } from "./_client";

/* -------------------------------------------------------------------------
 * Wire types — match the backend row dict 1:1.
 * ------------------------------------------------------------------------- */

/**
 * One row from the ``resources`` table as exposed to admin consumers.
 *
 * ``health_status`` is one of ``'healthy' | 'watch' | 'flagged' |
 * 'hidden'`` — kept as a plain string here so the UI can render
 * future statuses without a client redeploy. ``user_curated_at`` is
 * server-stamped (ISO-8601 UTC) on every write; ``null`` only for
 * legacy rows that predate the admin surface.
 */
export interface Resource {
  id: number;
  name: string;
  category: string;
  subcategory: string | null;
  address: string | null;
  lat: number | null;
  lng: number | null;
  phone: string | null;
  url: string | null;
  eligibility: string | null;
  services: string | null;
  hours: string | null;
  notes: string | null;
  city: string;
  barrier_affinity: string | null;
  health_status: string;
  user_curated_at: string | null;
}

/**
 * Paginated list response. ``limit`` + ``offset`` are echoed so the UI
 * can render "showing N–M of total" without re-deriving them.
 */
export interface ResourceListResponse {
  items: Resource[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * POST body for :func:`createResource`. Mirrors the backend
 * ``CreateResourceBody`` Pydantic model — required: ``name``,
 * ``category``, ``city``; optional fields cover the writable subset.
 * ``health_status`` is forced server-side; ``user_curated_at`` is
 * stamped server-side; neither is client-supplied.
 */
export interface CreateResourcePayload {
  name: string;
  category: string;
  city: string;
  subcategory?: string | null;
  address?: string | null;
  lat?: number | null;
  lng?: number | null;
  phone?: string | null;
  url?: string | null;
  eligibility?: string | null;
  services?: string | null;
  hours?: string | null;
  notes?: string | null;
  barrier_affinity?: string | null;
}

/**
 * PATCH body for :func:`updateResource` — partial update; every field
 * optional. The backend stamps ``user_curated_at`` even when no other
 * field changes (touch-as-curation semantics).
 */
export interface UpdateResourcePatch {
  name?: string;
  category?: string;
  city?: string;
  subcategory?: string | null;
  address?: string | null;
  lat?: number | null;
  lng?: number | null;
  phone?: string | null;
  url?: string | null;
  eligibility?: string | null;
  services?: string | null;
  hours?: string | null;
  notes?: string | null;
  barrier_affinity?: string | null;
}

/**
 * Response from :func:`restoreResource` — the backend echoes the
 * resulting state rather than re-fetching the whole row.
 */
export interface RestoreResourceResponse {
  id: number;
  health_status: string;
}

/* -------------------------------------------------------------------------
 * Error class — single typed discriminator for callers (status code).
 * ------------------------------------------------------------------------- */

export class AdminResourcesApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "AdminResourcesApiError";
    this.status = status;
    this.detail = detail;
  }
}

/* -------------------------------------------------------------------------
 * Internal helpers.
 * ------------------------------------------------------------------------- */

const BASE = "/api/admin/resources";

interface ListResourcesOpts {
  city?: string;
  limit?: number;
  offset?: number;
  includeHidden?: boolean;
}

/**
 * Build the ``?city=...&limit=...`` query string for :func:`listResources`.
 *
 * Returns ``""`` (no leading ``?``) when no opts are present so the URL
 * stays clean. ``includeHidden`` maps to the snake_case backend param
 * ``include_hidden`` — translation kept here so callers think in JS
 * conventions.
 */
function _buildListQuery(opts: ListResourcesOpts): string {
  const params = new URLSearchParams();
  if (opts.city !== undefined) params.set("city", opts.city);
  if (opts.limit !== undefined) params.set("limit", String(opts.limit));
  if (opts.offset !== undefined) params.set("offset", String(opts.offset));
  if (opts.includeHidden !== undefined) {
    params.set("include_hidden", String(opts.includeHidden));
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

/* -------------------------------------------------------------------------
 * Public surface — one function per backend route.
 * ------------------------------------------------------------------------- */

export async function listResources(
  opts: ListResourcesOpts = {},
): Promise<ResourceListResponse> {
  const res = await fetchWithCookie(`${BASE}${_buildListQuery(opts)}`, {
    method: "GET",
  });
  await throwOnApiError(res, AdminResourcesApiError, "admin-resources");
  return (await res.json()) as ResourceListResponse;
}

export async function getResource(id: number): Promise<Resource> {
  const res = await fetchWithCookie(`${BASE}/${id}`, { method: "GET" });
  await throwOnApiError(res, AdminResourcesApiError, "admin-resources");
  return (await res.json()) as Resource;
}

export async function createResource(
  payload: CreateResourcePayload,
): Promise<Resource> {
  const res = await fetchWithCookie(BASE, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await throwOnApiError(res, AdminResourcesApiError, "admin-resources");
  return (await res.json()) as Resource;
}

export async function updateResource(
  id: number,
  patch: UpdateResourcePatch,
): Promise<Resource> {
  const res = await fetchWithCookie(`${BASE}/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
  await throwOnApiError(res, AdminResourcesApiError, "admin-resources");
  return (await res.json()) as Resource;
}

export async function hideResource(id: number): Promise<void> {
  const res = await fetchWithCookie(`${BASE}/${id}`, { method: "DELETE" });
  await throwOnApiError(res, AdminResourcesApiError, "admin-resources");
}

export async function restoreResource(
  id: number,
): Promise<RestoreResourceResponse> {
  const res = await fetchWithCookie(`${BASE}/${id}/restore`, {
    method: "POST",
  });
  await throwOnApiError(res, AdminResourcesApiError, "admin-resources");
  return (await res.json()) as RestoreResourceResponse;
}
