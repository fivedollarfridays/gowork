/**
 * Typed API client for the admin claim-review dashboard (T24.9).
 *
 * Four endpoints, all mounted under ``/api/employers/admin/claims`` and
 * gated by ``require_role("admin")`` on the backend
 * (:mod:`app.routes.employers_admin`):
 *
 *   - GET    /pending             → admin queue
 *   - GET    /{claim_id}          → full claim+listing+employer detail
 *   - POST   /{claim_id}/approve  → promote employer to verified
 *   - DELETE /{claim_id}          → reject (delete claim + verification)
 *
 * Mirrors the fetch + timeout convention from `lib/api/assessments.ts`,
 * including the `_composeSignal` fix from S22 review-fixes that keeps
 * the timeout active when the caller passes their own AbortSignal.
 *
 * All non-2xx responses raise :class:`ListingClaimsApiError` so callers
 * can branch on `.status` (403 → not-authorised, 404 → missing).
 */

import { fetchWithCookie, throwOnApiError } from "./_client";

/* -------------------------------------------------------------------------
 * Wire types — match the backend dict shapes 1:1.
 * ------------------------------------------------------------------------- */

export interface PendingClaim {
  claim_id: number;
  claimant_email: string;
  listing_id: number;
  listing_title: string;
  employer_account_id: number;
  employer_name: string;
  employer_domain: string | null;
  verification_tier: string;
  intake_completed_at: string | null;
  verification_id: number;
  verification_created_at: string;
  claim_created_at: string;
}

export interface ClaimDetail {
  claim_id: number;
  claimant_email: string;
  listing_id: number;
  listing_title: string;
  listing_company: string | null;
  claim_created_at: string;
  expires_at: string;
  used_at: string | null;
  verification_id: number | null;
  employer_account_id: number | null;
  employer_name: string | null;
  employer_domain: string | null;
  employer_status: string | null;
  verification_tier: string | null;
  intake_json: string | null;
  intake_completed_at: string | null;
  verified_at: string | null;
}

export interface ApproveResponse {
  claim_id: number;
  employer_account_id: number | null;
  verification_status: string;
  verified_at: string;
}

/* -------------------------------------------------------------------------
 * Error class — single discriminator for callers (status code).
 * ------------------------------------------------------------------------- */

export class ListingClaimsApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "ListingClaimsApiError";
    this.status = status;
    this.detail = detail;
  }
}

/* -------------------------------------------------------------------------
 * Public surface — four typed functions consumed by the dashboard pages.
 * ------------------------------------------------------------------------- */

export async function listPendingClaims(): Promise<PendingClaim[]> {
  const res = await fetchWithCookie(
    "/api/employers/admin/claims/pending",
    { method: "GET" },
  );
  await throwOnApiError(res, ListingClaimsApiError, "listing-claims");
  return (await res.json()) as PendingClaim[];
}

export async function getClaim(claimId: number): Promise<ClaimDetail> {
  const res = await fetchWithCookie(
    `/api/employers/admin/claims/${claimId}`,
    { method: "GET" },
  );
  await throwOnApiError(res, ListingClaimsApiError, "listing-claims");
  return (await res.json()) as ClaimDetail;
}

export async function approveClaim(
  claimId: number,
): Promise<ApproveResponse> {
  const res = await fetchWithCookie(
    `/api/employers/admin/claims/${claimId}/approve`,
    { method: "POST" },
  );
  await throwOnApiError(res, ListingClaimsApiError, "listing-claims");
  return (await res.json()) as ApproveResponse;
}

export async function rejectClaim(claimId: number): Promise<void> {
  const res = await fetchWithCookie(
    `/api/employers/admin/claims/${claimId}`,
    { method: "DELETE" },
  );
  await throwOnApiError(res, ListingClaimsApiError, "listing-claims");
}
