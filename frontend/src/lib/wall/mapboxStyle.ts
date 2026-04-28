/**
 * T2.18 — Mapbox style URL resolution + fallback chain.
 *
 * The Wall renders against a custom dark editorial Mapbox style built in
 * Mapbox Studio (manual, one-time setup — see
 * `docs/runbooks/mapbox-style-setup.md`). The resulting style URL is wired
 * via the public env var `NEXT_PUBLIC_MAPBOX_STYLE_URL` so the deploy can
 * swap styles without code changes (multi-city, A/B, hotfix paths).
 *
 * Resolution rules (in order):
 *   1. Use `NEXT_PUBLIC_MAPBOX_STYLE_URL` if it's a non-blank `mapbox://`
 *      URI.
 *   2. Otherwise fall back to Mapbox's stock dark style.
 *
 * The light variant is exported for W3 (the `/assess` + `/plan` View
 * Transitions need a non-dark base). It's referenced now so the W2/W3
 * boundary is clear.
 *
 * Spotlight (Honesty + Legacy Lens — Driver A): the runbook lives next to
 * the code; if Studio access is lost, the JSON export under
 * `frontend/data/mapbox-style-export.json` is the recovery artifact.
 */

/** The fallback dark style — Mapbox's stock dark-v11. Always available. */
export const FALLBACK_DARK_STYLE_URL = "mapbox://styles/mapbox/dark-v11";

/** Light variant fallback — used by `/assess` + `/plan` (W3). */
export const FALLBACK_LIGHT_STYLE_URL = "mapbox://styles/mapbox/light-v11";

/** Mapbox Studio style URIs always start with this scheme. */
const STUDIO_PREFIX = "mapbox://styles/";

/**
 * Resolve the Mapbox style URL `MapboxScene` should mount.
 *
 * Pure function — no network, no side effects. Safe in render paths.
 * Validates the env var so a misconfigured deploy can't redirect the map
 * to an attacker-controlled style.json (URL spoofing defense).
 */
export function resolveMapboxStyleUrl(): string {
  const raw = process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL;
  if (typeof raw !== "string") return FALLBACK_DARK_STYLE_URL;
  const trimmed = raw.trim();
  if (trimmed.length === 0) return FALLBACK_DARK_STYLE_URL;
  if (!trimmed.startsWith(STUDIO_PREFIX)) return FALLBACK_DARK_STYLE_URL;
  return trimmed;
}
