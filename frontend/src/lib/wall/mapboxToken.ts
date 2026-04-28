/**
 * T2.1 — Mapbox token validation + static fallback chain.
 *
 * The W2 Wall lane needs a SINGLE choke point that decides whether to mount
 * the live Mapbox map or the static Fort Worth screenshot fallback. W1
 * shipped a sync shape-check (`validateMapboxToken` in `./env`); W2 layers a
 * network probe on top so we ALSO catch CDN outages, malformed API
 * responses, and slow networks. Without the network probe, a chapter could
 * try to mount Mapbox while the CDN is down — and the whole page breaks.
 *
 * Three failure modes the static fallback absorbs:
 *   1. Token missing / blank
 *   2. Token malformed (not a public `pk.` token)
 *   3. Mapbox CDN unreachable (timeout, 5xx, fetch throw)
 *
 * Spotlight (Root Cause Lens — Driver A): one choke point, three branches,
 * three test paths. Every chapter that consumes Mapbox subscribes here.
 */

import { validateMapboxToken } from "./env";

/** Mapbox public CDN — this is the canonical "is the API up?" health probe. */
const PROBE_URL = "https://api.mapbox.com/v1/styles/v1/mapbox/dark-v11";

/** Network probe timeout (ms). Aligned with W1 `--motion-duration-baseline`
 *  of 280ms × 7 — long enough to absorb 4G latency, short enough that demo
 *  day judges don't see a stalled page. */
const PROBE_TIMEOUT_MS = 2_000;

/**
 * Sync shape-check on `NEXT_PUBLIC_MAPBOX_TOKEN`.
 *
 * Returns `true` only when the env var is set AND starts with `pk.`. Never
 * makes a network call; safe to use in render paths and SSR.
 */
export function validateToken(): boolean {
  return validateMapboxToken().ok;
}

/**
 * Async network-aware availability check.
 *
 * Returns `true` only when:
 *   - the token passes `validateToken()`, AND
 *   - a probe to `api.mapbox.com` returns 2xx within 2s.
 *
 * Never throws. Any failure mode (timeout, 5xx, fetch reject) collapses to
 * `false` so callers can render the static fallback without try/catch.
 */
export async function isMapboxAvailable(): Promise<boolean> {
  if (!validateToken()) return false;

  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN as string;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);

  try {
    const url = `${PROBE_URL}?access_token=${encodeURIComponent(token)}`;
    const response = await fetch(url, { signal: controller.signal });
    return response.ok;
  } catch {
    // Timeout (AbortError), network failure (TypeError), DNS — all fall back
    // silently. The static fallback path is the user-visible response.
    return false;
  } finally {
    clearTimeout(timer);
  }
}
