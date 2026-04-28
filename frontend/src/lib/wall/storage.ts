/**
 * Storage namespace (Wave 2 — cross-driver integration).
 *
 * One module owns every localStorage + sessionStorage key the Wall touches.
 * Driver A's tokens, Driver B's audio + RUM, Driver C's mute toggle + locale
 * toggle previously each declared their own STORAGE_KEY constant in their own
 * module — mute broke silently because two modules disagreed on whether the
 * key was `gowork-muted` (hyphen, MuteToggle) or `gowork.muted` (dot, sound).
 *
 * Contract:
 *   - All Wall keys begin with `gowork.` (dot-separated namespace).
 *   - `montgowork-` legacy keys are kept for session continuity (locale only).
 *   - `getStored` / `setStored` are SSR-safe (no-op on the server).
 *   - Non-string values pass through JSON for write + read; if parse fails,
 *     the fallback is returned (corruption is not the caller's problem).
 *
 * Refactor consumers:
 *   - `MuteToggle.tsx` reads/writes via STORAGE_KEYS.MUTED.
 *   - `sound.ts` reads via STORAGE_KEYS.MUTED.
 *   - `useLanguage.ts` reads/writes via STORAGE_KEYS.LOCALE + LOCALE_LEGACY.
 *   - `analytics/session-id.ts` reads/writes via STORAGE_KEYS.RUM_SID
 *     (sessionStorage-bound; helper covers localStorage; session-id manages
 *     its own sessionStorage so the constant is shared but I/O is not).
 */

export const STORAGE_KEYS = {
  /** Preferred locale (en | es). New writes use this. */
  LOCALE: "gowork.locale",
  /** Legacy MontGoWork locale key — read for session continuity, dual-written. */
  LOCALE_LEGACY: "montgowork-locale",
  /** Mute preference for Howler audio. Default: true (muted). */
  MUTED: "gowork.muted",
  /** RUM session id (sessionStorage). 64-char hex hash. */
  RUM_SID: "gowork.rum.sid",
  /** Cached Mapbox token validation result. */
  MAPBOX_TOKEN_VALIDATED: "gowork.mapbox.validated",
} as const;

export type StorageKey = (typeof STORAGE_KEYS)[keyof typeof STORAGE_KEYS];

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof localStorage !== "undefined";
}

/** Read a stored value. Strings round-trip; objects/arrays JSON-decode. */
export function getStored<T>(key: string, fallback: T): T {
  if (!isBrowser()) return fallback;
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return fallback;
    if (typeof fallback === "string") return raw as unknown as T;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

/** Write a value. Strings stored verbatim; non-strings JSON-encoded. */
export function setStored(key: string, value: unknown): void {
  if (!isBrowser()) return;
  try {
    const raw = typeof value === "string" ? value : JSON.stringify(value);
    localStorage.setItem(key, raw);
  } catch {
    /* private browsing / quota exceeded — caller-state authoritative */
  }
}

/** Delete a key. Idempotent. */
export function removeStored(key: string): void {
  if (!isBrowser()) return;
  try {
    localStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}
