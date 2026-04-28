/**
 * T1.6 — Mapbox token boot validator.
 *
 * W2's WallContainer reads this at module init. When the token is missing
 * or malformed, the container falls back to T1.74's static branded
 * placeholder instead of failing loudly in the browser.
 *
 * SSR-safe: no window/document/localStorage access. process.env is the
 * sole input — Next.js inlines NEXT_PUBLIC_MAPBOX_TOKEN at build time.
 *
 * Security: rejects sk.* (private tokens) — those would leak in the bundle.
 * The frontend public token MUST start with `pk.`.
 */

export interface MapboxTokenValidation {
  ok: boolean;
  reason?: string;
}

export function validateMapboxToken(): MapboxTokenValidation {
  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  if (token === undefined || token === null || token === "") {
    return { ok: false, reason: "NEXT_PUBLIC_MAPBOX_TOKEN is unset or empty" };
  }
  if (token.startsWith("sk.")) {
    return {
      ok: false,
      reason: "Token is a private (sk.) token — must use a public (pk.) token on the frontend",
    };
  }
  if (!token.startsWith("pk.")) {
    return {
      ok: false,
      reason: "Token has an invalid format — Mapbox public tokens start with 'pk.'",
    };
  }
  return { ok: true };
}
