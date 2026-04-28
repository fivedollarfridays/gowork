/**
 * Network profile utility (T1.99).
 *
 * Reads `navigator.connection` (Network Information API). Mostly
 * Chromium; Safari + Firefox return undefined and we degrade to a
 * "saveData=false, effectiveType='unknown'" baseline so the W2 fallback
 * decision tree always has a stable input shape.
 *
 * Used by W2 to decide between Mapbox vector tiles (4g) and a static
 * raster preview (2g/3g/saveData), and by W3 to gate the 3D barrier
 * graph behind a connection-quality check.
 *
 * SSR-safe: server returns `{ saveData: false, effectiveType: 'unknown',
 * downlinkMbps: null }`.
 */

export type EffectiveType = "2g" | "3g" | "4g" | "unknown";

export interface NetworkProfile {
  saveData: boolean;
  effectiveType: EffectiveType;
  downlinkMbps: number | null;
}

const KNOWN_EFFECTIVE_TYPES: ReadonlySet<EffectiveType> = new Set(["2g", "3g", "4g"]);

interface ConnectionLike {
  saveData?: boolean;
  effectiveType?: string;
  downlink?: number;
}

function readConnection(): ConnectionLike | null {
  if (typeof navigator === "undefined") return null;
  const conn = (navigator as unknown as { connection?: ConnectionLike }).connection;
  return conn ?? null;
}

function normalizeEffectiveType(raw: string | undefined): EffectiveType {
  if (!raw) return "unknown";
  const lower = raw.toLowerCase() as EffectiveType;
  return KNOWN_EFFECTIVE_TYPES.has(lower) ? lower : "unknown";
}

/** Snapshot the current network profile. Synchronous + cheap. */
export function getNetworkProfile(): NetworkProfile {
  const conn = readConnection();
  if (!conn) {
    return { saveData: false, effectiveType: "unknown", downlinkMbps: null };
  }
  return {
    saveData: Boolean(conn.saveData),
    effectiveType: normalizeEffectiveType(conn.effectiveType),
    downlinkMbps: typeof conn.downlink === "number" ? conn.downlink : null,
  };
}

/** Convenience boolean — `true` when the user opted into Save-Data. */
export function isSaveDataOn(): boolean {
  return getNetworkProfile().saveData;
}

/** Convenience boolean — `true` when network is 2g/3g (slow lane). */
export function isSlowConnection(): boolean {
  const t = getNetworkProfile().effectiveType;
  return t === "2g" || t === "3g";
}
