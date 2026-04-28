/**
 * RUM session id (T1.81).
 *
 * Generates a per-tab session id by hashing the user-agent + screen
 * dimensions + a per-tab nonce with SHA-256. Stored in sessionStorage
 * (NOT localStorage) so closing the tab ends the session — short-lived
 * by design.
 *
 * Privacy contract: we never store raw user-agent or any non-hashed
 * fingerprint material. The 64-char hex hash IS the only identifier.
 */

import { STORAGE_KEYS } from "@/lib/wall/storage";

export const SESSION_STORAGE_KEY = STORAGE_KEYS.RUM_SID;

let inMemoryId: string | null = null;
let inFlight: Promise<string> | null = null;

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof sessionStorage !== "undefined";
}

function readPersistedId(): string | null {
  if (!isBrowser()) return null;
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (raw && /^[0-9a-f]{64}$/.test(raw)) return raw;
  } catch {
    /* ignore */
  }
  return null;
}

function persistId(id: string): void {
  if (!isBrowser()) return;
  try {
    sessionStorage.setItem(SESSION_STORAGE_KEY, id);
  } catch {
    /* ignore */
  }
}

function bytesToHex(bytes: ArrayBuffer | Uint8Array): string {
  const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let hex = "";
  for (const b of arr) hex += b.toString(16).padStart(2, "0");
  return hex;
}

/** SHA-256 via Web Crypto when available, else a non-crypto fallback. */
async function hashString(input: string): Promise<string> {
  const subtle = (globalThis.crypto as unknown as { subtle?: SubtleCrypto }).subtle;
  if (subtle && typeof subtle.digest === "function") {
    const buf = new TextEncoder().encode(input);
    const digest = await subtle.digest("SHA-256", buf);
    return bytesToHex(digest);
  }
  // Fallback: 64-char hex from a non-crypto FNV-style mix repeated to fill.
  let h = 0xcbf29ce484222325n;
  const prime = 0x100000001b3n;
  for (const ch of input) {
    h = ((h ^ BigInt(ch.charCodeAt(0))) * prime) & 0xffffffffffffffffn;
  }
  let hex = h.toString(16).padStart(16, "0");
  while (hex.length < 64) hex += hex;
  return hex.slice(0, 64);
}

function fingerprintInput(): string {
  const ua = typeof navigator !== "undefined" ? navigator.userAgent : "node";
  const w = typeof screen !== "undefined" ? screen.width : 0;
  const h = typeof screen !== "undefined" ? screen.height : 0;
  const nonce =
    (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random()}`);
  return `${ua}|${w}x${h}|${nonce}`;
}

/**
 * Get the current tab's RUM session id. Resolves to a 64-char hex string
 * on the client, or `'ssr'` on the server.
 *
 * Idempotent within a tab — subsequent calls return the cached id until
 * sessionStorage is cleared.
 */
export async function getSessionId(): Promise<string> {
  if (!isBrowser()) return "ssr";
  if (inMemoryId) return inMemoryId;
  const persisted = readPersistedId();
  if (persisted) {
    inMemoryId = persisted;
    return persisted;
  }
  if (inFlight) return inFlight;
  inFlight = (async () => {
    const hash = await hashString(fingerprintInput());
    inMemoryId = hash;
    persistId(hash);
    inFlight = null;
    return hash;
  })();
  return inFlight;
}

/** Reset cached id (tests only). */
export function _resetSessionForTests(): void {
  inMemoryId = null;
  inFlight = null;
}
