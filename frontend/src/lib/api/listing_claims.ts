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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const REQUEST_TIMEOUT_MS = 30_000;

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
 * Internal fetch helpers — mirrors lib/api/assessments.ts.
 * ------------------------------------------------------------------------- */

function _composeSignal(
  callerSignal: AbortSignal | null | undefined,
  timeoutSignal: AbortSignal,
): AbortSignal {
  if (!callerSignal) return timeoutSignal;
  if (typeof AbortSignal.any === "function") {
    return AbortSignal.any([callerSignal, timeoutSignal]);
  }
  const relay = new AbortController();
  const onAbort = () => relay.abort();
  if (callerSignal.aborted || timeoutSignal.aborted) {
    relay.abort();
  } else {
    callerSignal.addEventListener("abort", onAbort, { once: true });
    timeoutSignal.addEventListener("abort", onAbort, { once: true });
  }
  return relay.signal;
}

async function _fetchWithTimeout(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const headers: HeadersInit = { ...(init?.headers ?? {}) };
  if (init?.body) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      ...init,
      headers,
      signal: _composeSignal(init?.signal, controller.signal),
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

async function _throwOnError(res: Response): Promise<void> {
  if (res.ok) return;
  const body = await res.json().catch(() => ({ detail: res.statusText }));
  const detail = typeof body?.detail === "string" ? body.detail : undefined;
  throw new ListingClaimsApiError(
    res.status,
    detail ?? `listing-claims API error ${res.status}`,
    detail,
  );
}

/* -------------------------------------------------------------------------
 * Public surface — four typed functions consumed by the dashboard pages.
 * ------------------------------------------------------------------------- */

export async function listPendingClaims(): Promise<PendingClaim[]> {
  const res = await _fetchWithTimeout(
    "/api/employers/admin/claims/pending",
    { method: "GET" },
  );
  await _throwOnError(res);
  return (await res.json()) as PendingClaim[];
}

export async function getClaim(claimId: number): Promise<ClaimDetail> {
  const res = await _fetchWithTimeout(
    `/api/employers/admin/claims/${claimId}`,
    { method: "GET" },
  );
  await _throwOnError(res);
  return (await res.json()) as ClaimDetail;
}

export async function approveClaim(
  claimId: number,
): Promise<ApproveResponse> {
  const res = await _fetchWithTimeout(
    `/api/employers/admin/claims/${claimId}/approve`,
    { method: "POST" },
  );
  await _throwOnError(res);
  return (await res.json()) as ApproveResponse;
}

export async function rejectClaim(claimId: number): Promise<void> {
  const res = await _fetchWithTimeout(
    `/api/employers/admin/claims/${claimId}`,
    { method: "DELETE" },
  );
  await _throwOnError(res);
}
