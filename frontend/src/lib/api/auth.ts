/**
 * Typed API client for the GoWork Identity / magic-link surface (T22.10).
 *
 * Two endpoints:
 *   - POST /api/auth/magic-link {email}  → 202 Accepted (always — no enumeration)
 *   - GET  /api/auth/claim?token=…       → 200 success, 401 invalid, 409 conflict
 *
 * The backend pairs with T22.7 (magic-link request) and T22.8 (claim).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const REQUEST_TIMEOUT_MS = 30_000;

export interface ClaimSuccess {
  account_id: number;
  claimed_session_ids: string[];
}

/**
 * Discriminated error for the claim endpoint. The page renders different
 * UI for each kind, so we surface the bucket explicitly rather than
 * forcing the caller to sniff status codes from a generic Error.
 */
export type ClaimErrorKind = "invalid" | "conflict" | "unknown";

export class ClaimError extends Error {
  readonly kind: ClaimErrorKind;
  readonly status: number;

  constructor(kind: ClaimErrorKind, status: number, message?: string) {
    super(message ?? `claim failed (${status})`);
    this.name = "ClaimError";
    this.kind = kind;
    this.status = status;
  }
}

function _classifyClaimStatus(status: number): ClaimErrorKind {
  if (status === 401) return "invalid";
  if (status === 409) return "conflict";
  return "unknown";
}

/**
 * Fetch with a hard timeout. Mirrors the convention in
 * `lib/api/appointments.ts` so behaviour stays consistent across the
 * frontend. Returns the raw Response so callers can branch on status.
 */
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
      ...init,
      headers,
      signal: init?.signal ?? controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * POST /api/auth/magic-link {email}.
 *
 * The backend ALWAYS returns 202 (intentional — prevents account
 * enumeration via timing/response shape). We resolve on any 2xx and
 * swallow the body. The page renders the same "check your inbox"
 * confirmation regardless of outcome.
 */
export async function requestMagicLink(email: string): Promise<void> {
  const res = await _fetchWithTimeout("/api/auth/magic-link", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    // Non-2xx is unexpected (the endpoint is designed to always return
    // 202). Swallow the body to avoid leaking detail to the UI; the
    // login page still shows the success screen for parity with the
    // happy path. The mutation hook can choose to surface errors if it
    // ever wants to (rate-limit 429 might be the one exception).
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `API error ${res.status}`);
  }
}

/**
 * GET /api/auth/claim?token=…
 *
 * Returns the claimed account on success. Throws ``ClaimError`` for
 * 401/409/other non-2xx so the page can render the appropriate state
 * machine branch. Sends ``credentials: "include"`` so the browser keeps
 * the ``gw_account`` cookie set by the backend on success.
 */
export async function claimMagicLink(token: string): Promise<ClaimSuccess> {
  const url = `/api/auth/claim?token=${encodeURIComponent(token)}`;
  const res = await _fetchWithTimeout(url, {
    method: "GET",
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ClaimError(
      _classifyClaimStatus(res.status),
      res.status,
      typeof body?.detail === "string" ? body.detail : undefined,
    );
  }
  return (await res.json()) as ClaimSuccess;
}
