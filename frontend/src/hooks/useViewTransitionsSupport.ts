"use client";

import { useState, useEffect } from "react";

/**
 * Returns `true` when the View Transitions API is available
 * (`document.startViewTransition`).
 *
 * SSR-safe: returns `false` on the server. Evaluated once on mount —
 * the API does not appear or disappear within a session.
 *
 * Used by W3 Chapter 10 to choose between a morph transition and
 * a standard navigation. Also used by W2 to gate map view-state animations.
 */
export function useViewTransitionsSupport(): boolean {
  const [supported, setSupported] = useState<boolean>(false);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const candidate = (document as unknown as { startViewTransition?: unknown })
      .startViewTransition;
    setSupported(typeof candidate === "function");
  }, []);

  return supported;
}
