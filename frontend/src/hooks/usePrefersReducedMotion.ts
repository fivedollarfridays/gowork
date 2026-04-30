"use client";

import { useEffect, useState } from "react";

const MEDIA_QUERY = "(prefers-reduced-motion: reduce)";

/**
 * Returns `true` when the user has enabled the "reduce motion" OS setting.
 *
 * SSR-safe: renders `false` on the server (fail-open to motion enabled —
 * most users have it OFF). Subscribes to changes via `matchMedia.change`
 * so a mid-session preference toggle propagates without a reload.
 *
 * Used by every animation site in W2/W3/W4.
 *
 * @example
 * const reduceMotion = usePrefersReducedMotion();
 * <motion.div animate={reduceMotion ? undefined : { opacity: [0, 1] }} />
 */
export function usePrefersReducedMotion(): boolean {
  const [prefers, setPrefers] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const mql = window.matchMedia(MEDIA_QUERY);
    setPrefers(mql.matches);

    const handler = (event: MediaQueryListEvent) => setPrefers(event.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return prefers;
}
