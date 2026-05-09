/**
 * Typed API client for the admin-feedback surfaces (T26.6).
 *
 * Five endpoints under ``/api/admin/feedback`` (backend
 * :mod:`app.routes.admin_feedback`, T26.3), all gated by
 * ``require_role("admin")`` on the cookie session. Two read surfaces
 * + three mutations:
 *
 *   - GET  /flagged?city=<slug>                       — flagged-resource queue
 *   - POST /flagged/{id}/approve                      — clear flag → healthy
 *   - POST /flagged/{id}/confirm-hide                 — soft-hide → hidden
 *   - GET  /visits?reviewed=<bool>&limit=&offset=     — visit-feedback inbox
 *   - POST /visits/{id}/mark-reviewed                 — flip reviewed + stamp
 *
 * Mirrors the S25 :file:`cities_admin.ts` shape post-/reviewing-and-fixing
 * lift: imports `fetchWithCookie` + `throwOnApiError` from `_client.ts`
 * (the shared transport added in PR #126), and contributes only the
 * typed wire types + a single per-domain error subclass. Per-domain
 * clients deliberately do NOT re-implement timeout / cookie / error
 * handling — that drift was the lesson of S22's three-times
 * `_composeSignal` fix.
 *
 * Charter: this is an admin-only diagnostic; matching-engine modules
 * are never imported. The T25.9 charter integrity test re-runs green
 * across this client because it only touches the feedback substrate.
 */

import { fetchWithCookie, throwOnApiError } from "./_client";

/* -------------------------------------------------------------------------
 * Wire types — match the backend response shapes 1:1.
 *
 * Source of truth: :func:`app.core.queries_admin_feedback.list_flagged_resources`
 * and :func:`list_visit_feedback`. Nullable columns are typed as
 * ``T | null`` because SQLite + Postgres both surface NULL columns as
 * `null` through SQLAlchemy's ``_mapping`` proxy.
 * ------------------------------------------------------------------------- */

/**
 * One row of recent negative ``resource_feedback`` (last 30 days),
 * attached to each flagged resource for context.
 */
export interface NegativeFeedbackEntry {
  session_id: string;
  barrier_type: string | null;
  submitted_at: string;
}

export interface FlaggedResource {
  id: number;
  name: string;
  category: string | null;
  city: string | null;
  health_status: string;
  address: string | null;
  phone: string | null;
  url: string | null;
  recent_negative_feedback: NegativeFeedbackEntry[];
}

export interface FlaggedResourcesResponse {
  items: FlaggedResource[];
}

export interface FlaggedActionResponse {
  id: number;
  health_status: string;
}

/**
 * One row of ``visit_feedback`` as returned by the inbox endpoint.
 *
 * ``made_it_to_center`` and ``reviewed`` come back as integers (0/1)
 * from the SQLite + Postgres queries; the UI is responsible for the
 * boolean cast at render time. ``plan_accuracy`` is the 1–5 star value
 * from m001; nullable for legacy rows pre-rating.
 */
export interface VisitFeedback {
  id: number;
  session_id: string;
  submitted_at: string;
  made_it_to_center: number;
  outcomes: string | null;
  plan_accuracy: number | null;
  free_text: string | null;
  reviewed: number;
  action_taken: string | null;
}

export interface VisitFeedbackListResponse {
  items: VisitFeedback[];
  total: number;
  limit: number;
  offset: number;
}

export interface MarkReviewedResponse {
  id: number;
  reviewed: boolean;
  action_taken: string | null;
}

/* -------------------------------------------------------------------------
 * Error class — single discriminator (status code + optional detail).
 * ------------------------------------------------------------------------- */

export class AdminFeedbackApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "AdminFeedbackApiError";
    this.status = status;
    this.detail = detail;
  }
}

/* -------------------------------------------------------------------------
 * Public surface — five typed functions consumed by the T26.9 page.
 * ------------------------------------------------------------------------- */

export async function listFlagged(
  city: string,
): Promise<FlaggedResourcesResponse> {
  const qs = new URLSearchParams({ city }).toString();
  const res = await fetchWithCookie(
    `/api/admin/feedback/flagged?${qs}`,
    { method: "GET" },
  );
  await throwOnApiError(res, AdminFeedbackApiError, "admin-feedback");
  return (await res.json()) as FlaggedResourcesResponse;
}

export async function approveFlagged(
  resourceId: number,
): Promise<FlaggedActionResponse> {
  const res = await fetchWithCookie(
    `/api/admin/feedback/flagged/${resourceId}/approve`,
    { method: "POST" },
  );
  await throwOnApiError(res, AdminFeedbackApiError, "admin-feedback");
  return (await res.json()) as FlaggedActionResponse;
}

export async function confirmHide(
  resourceId: number,
): Promise<FlaggedActionResponse> {
  const res = await fetchWithCookie(
    `/api/admin/feedback/flagged/${resourceId}/confirm-hide`,
    { method: "POST" },
  );
  await throwOnApiError(res, AdminFeedbackApiError, "admin-feedback");
  return (await res.json()) as FlaggedActionResponse;
}

export interface ListVisitsOptions {
  reviewed?: boolean;
  limit?: number;
  offset?: number;
}

export async function listVisits(
  opts: ListVisitsOptions = {},
): Promise<VisitFeedbackListResponse> {
  const params = new URLSearchParams();
  if (opts.reviewed !== undefined) {
    params.set("reviewed", String(opts.reviewed));
  }
  if (opts.limit !== undefined) params.set("limit", String(opts.limit));
  if (opts.offset !== undefined) params.set("offset", String(opts.offset));
  const qs = params.toString();
  const path = qs
    ? `/api/admin/feedback/visits?${qs}`
    : `/api/admin/feedback/visits`;
  const res = await fetchWithCookie(path, { method: "GET" });
  await throwOnApiError(res, AdminFeedbackApiError, "admin-feedback");
  return (await res.json()) as VisitFeedbackListResponse;
}

export async function markVisitReviewed(
  visitId: number,
  actionTaken?: string,
): Promise<MarkReviewedResponse> {
  // The backend route accepts an optional body; sending no body when
  // `actionTaken` is omitted matches the FastAPI ``MarkReviewedBody | None``
  // signature and keeps the Content-Type header off the wire (no body =>
  // no auto-JSON header from `_client`).
  const init: RequestInit =
    actionTaken !== undefined
      ? { method: "POST", body: JSON.stringify({ action_taken: actionTaken }) }
      : { method: "POST" };
  const res = await fetchWithCookie(
    `/api/admin/feedback/visits/${visitId}/mark-reviewed`,
    init,
  );
  await throwOnApiError(res, AdminFeedbackApiError, "admin-feedback");
  return (await res.json()) as MarkReviewedResponse;
}
