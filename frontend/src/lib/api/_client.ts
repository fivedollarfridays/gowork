/**
 * Shared low-level fetch primitives for typed API clients.
 *
 * Every typed API client (auth.ts, assessments.ts, listing_claims.ts,
 * and future S25+ clients) needs the same three things:
 *
 *   1. A base URL drawn from `NEXT_PUBLIC_API_URL`.
 *   2. A hard request timeout that survives caller-supplied AbortSignals.
 *   3. A way to derive a typed error class from a non-2xx response.
 *
 * Originally each client copy-pasted these. The `_composeSignal` fix
 * (S22 review-fix) had to be applied three times before this module
 * existed — that's the kind of drift this consolidation prevents.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const REQUEST_TIMEOUT_MS = 30_000;

/**
 * Combine caller-provided AbortSignal with our timeout signal.
 *
 * Without this, passing `signal` from the caller silently disabled
 * the timeout (the older `init?.signal ?? controller.signal` form
 * fell through to the caller's signal whenever it existed). Aborting
 * either signal aborts the resulting one. Uses `AbortSignal.any`
 * when available, with a relay-controller fallback for older
 * runtimes (Node < 20.3, Safari pre-17).
 */
export function composeSignal(
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

/**
 * Fetch with a hard timeout. Returns the raw Response so callers can
 * branch on status. Sets `Content-Type: application/json` when a body
 * is present (matches every API client's convention).
 */
export async function fetchWithTimeout(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const headers: HeadersInit = { ...(init?.headers ?? {}) };
  if (init?.body) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS,
  );
  try {
    return await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
      signal: composeSignal(init?.signal, controller.signal),
    });
  } finally {
    clearTimeout(timeoutId);
  }
}
