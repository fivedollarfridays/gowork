/**
 * Mapbox token boot validator (T1.6).
 *
 * The Wall (W2+) requires a Mapbox public token to render the interactive
 * map. This module is the SINGLE source of truth for whether Mapbox is
 * available — `WallContainer` will read `validateMapboxToken()` and decide
 * between mounting the live map or the static `MapboxTokenMissing`
 * fallback (T1.74).
 *
 * SSR-safe: `process.env` reads work in both Node and the browser because
 * Next.js inlines `NEXT_PUBLIC_*` vars at build time.
 */

const MAPBOX_PUBLIC_PREFIX = "pk.";

export interface MapboxTokenCheck {
  ok: boolean;
  reason?: string;
}

/** Read the configured Mapbox token from env. Returns null when absent/blank. */
export function getMapboxToken(): string | null {
  const raw = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  if (typeof raw !== "string" || raw.length === 0) return null;
  return raw;
}

/**
 * Validate that the configured Mapbox token is a public token.
 *
 * Public Mapbox tokens always start with `pk.` (per Mapbox docs).
 * Secret tokens (`sk.`) MUST NOT be exposed to the browser; we explicitly
 * reject them here so a misconfigured deploy fails loud and early.
 */
export function validateMapboxToken(): MapboxTokenCheck {
  const token = getMapboxToken();
  if (token === null) {
    return { ok: false, reason: "NEXT_PUBLIC_MAPBOX_TOKEN is not set." };
  }
  if (!token.startsWith(MAPBOX_PUBLIC_PREFIX)) {
    return {
      ok: false,
      reason: `Mapbox token must start with "${MAPBOX_PUBLIC_PREFIX}" (public token).`,
    };
  }
  return { ok: true };
}

/** Convenience boolean — `true` when the Wall can mount the live map. */
export function isMapboxAvailable(): boolean {
  return validateMapboxToken().ok;
}
