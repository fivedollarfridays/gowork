"use client";

import { useEffect, useState } from "react";

/**
 * polish-2 T58 — Network-aware effective-connection hook.
 *
 * Reads `navigator.connection.effectiveType` and maps it to an actionable
 * tri-state. Used by `ChapterRailTooltip` to skip the WebP preview when
 * the user is on a slow connection — Driver A consumes the hook there.
 *
 * Mapping:
 *   - "slow-2g" / "2g" → "slow"
 *   - "3g" / "4g"      → "fast"
 *   - anything else / API absent → "unknown"
 *
 * SSR-safe: returns `"unknown"` during the server render. Subscribes to
 * the `change` event when the API is available so callers see live
 * updates if the radio drops to 2g mid-session.
 */
export type EffectiveConnection = "slow" | "fast" | "unknown";

interface NetworkInformationLike {
  effectiveType?: string;
  addEventListener?: (type: string, fn: () => void) => void;
  removeEventListener?: (type: string, fn: () => void) => void;
}

function readEffectiveType(): EffectiveConnection {
  if (typeof navigator === "undefined") return "unknown";
  const conn = (navigator as unknown as { connection?: NetworkInformationLike })
    .connection;
  const t = conn?.effectiveType;
  if (t === "slow-2g" || t === "2g") return "slow";
  if (t === "3g" || t === "4g") return "fast";
  return "unknown";
}

export function useEffectiveConnection(): EffectiveConnection {
  const [value, setValue] = useState<EffectiveConnection>(() =>
    readEffectiveType(),
  );

  useEffect(() => {
    if (typeof navigator === "undefined") return;
    setValue(readEffectiveType());
    const conn = (navigator as unknown as {
      connection?: NetworkInformationLike;
    }).connection;
    if (!conn?.addEventListener) return;
    const sync = () => setValue(readEffectiveType());
    conn.addEventListener("change", sync);
    return () => conn.removeEventListener?.("change", sync);
  }, []);

  return value;
}
