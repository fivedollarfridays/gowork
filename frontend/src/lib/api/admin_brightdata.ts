/**
 * Typed API client for the BrightData admin trigger endpoints (T26.7).
 *
 * Two endpoints, both mounted under ``/api/brightdata`` and gated by
 * ``require_role("admin")`` on the backend (T26.4 — gate-migrated from
 * the legacy header-based ``require_admin_key``):
 *
 *   - POST /crawl                  → trigger a crawl job
 *   - GET  /status/{snapshot_id}   → poll snapshot status
 *
 * Wire types match :mod:`backend.app.integrations.brightdata.types` 1:1
 * — the Pydantic models there are the source of truth. Status enum
 * values reflect backend reality (`starting | running | ready | failed`).
 *
 * Mirrors the fetch + timeout + cookie-session convention from
 * :file:`lib/api/cities_admin.ts` (S25 lift): everything delegates to
 * :func:`fetchWithCookie` from `_client.ts` so the cookie session
 * reaches the gate, and non-2xx responses raise
 * :class:`AdminBrightDataApiError` so callers can branch on
 * ``.status`` (502 → upstream BrightData failure, 503 → not configured).
 */

import { fetchWithCookie, throwOnApiError } from "./_client";

/* -------------------------------------------------------------------------
 * Wire types — match backend Pydantic shapes 1:1.
 * ------------------------------------------------------------------------- */

/**
 * Snapshot lifecycle states emitted by the backend (`CrawlStatus` enum
 * in `app.integrations.brightdata.types`). `ready` means the crawl
 * completed and results were cached. `failed` is terminal.
 */
export type CrawlStatusValue = "starting" | "running" | "ready" | "failed";

/**
 * Body posted to ``POST /api/brightdata/crawl``. Backend enforces
 * HTTPS-only + no-private-IP via Pydantic validators on the
 * ``TriggerCrawlRequest`` model (SSRF prevention). Client passes the
 * URLs through as-is and surfaces the 422 if validation fails.
 */
export interface TriggerCrawlPayload {
  urls: string[];
}

/**
 * Response from ``POST /api/brightdata/crawl``. Returns immediately —
 * actual job results are fetched later via :func:`getCrawlStatus`.
 */
export interface TriggerCrawlResponse {
  snapshot_id: string;
  status: CrawlStatusValue;
  message: string;
}

/**
 * Response from ``GET /api/brightdata/status/{snapshot_id}``. Maps to
 * the backend's ``CrawlStatusResponse`` Pydantic model. ``progress_pct``
 * is populated while the snapshot is running; ``jobs_found`` is
 * populated once status flips to ``ready`` (the route auto-caches the
 * results into the local DB at that point).
 */
export interface CrawlStatus {
  snapshot_id: string;
  status: CrawlStatusValue;
  progress_pct: number | null;
  jobs_found: number | null;
  message: string;
}

/* -------------------------------------------------------------------------
 * Error class — single discriminator for callers (status code).
 * ------------------------------------------------------------------------- */

export class AdminBrightDataApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "AdminBrightDataApiError";
    this.status = status;
    this.detail = detail;
  }
}

/* -------------------------------------------------------------------------
 * Public surface — one function per backend route.
 * ------------------------------------------------------------------------- */

export async function triggerCrawl(
  payload: TriggerCrawlPayload,
): Promise<TriggerCrawlResponse> {
  const res = await fetchWithCookie("/api/brightdata/crawl", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await throwOnApiError(res, AdminBrightDataApiError, "admin-brightdata");
  return (await res.json()) as TriggerCrawlResponse;
}

export async function getCrawlStatus(
  snapshotId: string,
): Promise<CrawlStatus> {
  // Snapshot ids are constrained by the backend's Path() pattern
  // (alnum + ``_-``), but encode defensively so a stray ``/`` never
  // splits the path segment.
  const encoded = encodeURIComponent(snapshotId);
  const res = await fetchWithCookie(`/api/brightdata/status/${encoded}`, {
    method: "GET",
  });
  await throwOnApiError(res, AdminBrightDataApiError, "admin-brightdata");
  return (await res.json()) as CrawlStatus;
}
