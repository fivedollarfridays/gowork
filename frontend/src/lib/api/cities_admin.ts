/**
 * Typed API client for the DFW cross-metro admin diagnostic (T25.7).
 *
 * Single endpoint, mounted under ``/api/admin/cities`` and gated by
 * ``require_role("admin")`` on the backend
 * (:mod:`app.routes.cities_admin`):
 *
 *   - GET /summary  → per-city resource/employer/transit counts +
 *                     a ``dfw_total`` aggregate for the FW + Dallas
 *                     side-by-side admin page.
 *
 * Charter integrity (S25 / T25.7):
 *   This is a **display-only** diagnostic. The backend route reads
 *   counts from JSON seed files (``data/cities/<slug>/...``) — no DB
 *   queries, no matching-engine imports. The grep gate in T25.9 keeps
 *   the matching module clear of city-specific references; this client
 *   is the consumer side of the same charter.
 *
 * Mirrors the fetch + timeout convention from
 * :file:`lib/api/listing_claims.ts` (S24 DRY extraction): everything
 * delegates to :func:`fetchWithTimeout` from `_client.ts` and bakes in
 * `credentials: "include"` so the cookie session reaches the gate.
 */

import { fetchWithCookie, throwOnApiError } from "./_client";

/* -------------------------------------------------------------------------
 * Wire types — match the backend dict shapes 1:1.
 * ------------------------------------------------------------------------- */

/**
 * Resource counts keyed by category string (e.g. ``social_service``,
 * ``career_center``, ``childcare``). The backend zero-fills missing
 * categories so both cities expose the same key set — the page can
 * render parallel rows without re-keying the dict.
 */
export type ResourceCounts = Record<string, number>;

export interface CitySummary {
  slug: string;
  name: string;
  state: string;
  resource_counts: ResourceCounts;
  employer_count: number;
  fair_chance_count: number;
  /** Decimal fraction (0..1), pre-rounded to 4 places by the backend. */
  fair_chance_pct: number;
  transit_route_count: number;
  transit_stop_count: number;
  career_center_count: number;
}

export interface DfwTotal {
  resource_counts: ResourceCounts;
  employer_count: number;
  fair_chance_count: number;
  fair_chance_pct: number;
  transit_route_count: number;
  transit_stop_count: number;
  career_center_count: number;
}

export interface DfwSummaryResponse {
  cities: CitySummary[];
  dfw_total: DfwTotal;
}

/* -------------------------------------------------------------------------
 * Error class — single discriminator for callers (status code).
 * ------------------------------------------------------------------------- */

export class CitiesAdminApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "CitiesAdminApiError";
    this.status = status;
    this.detail = detail;
  }
}

/* -------------------------------------------------------------------------
 * Public surface — one typed function consumed by the DFW summary page.
 * ------------------------------------------------------------------------- */

export async function getDfwSummary(): Promise<DfwSummaryResponse> {
  const res = await fetchWithCookie("/api/admin/cities/summary", {
    method: "GET",
  });
  await throwOnApiError(res, CitiesAdminApiError, "cities-admin");
  return (await res.json()) as DfwSummaryResponse;
}
