"use client";

/**
 * T4.D.7 — IdleStateProvider (Wave 4 polish).
 *
 * Sets `data-life-idle="true"` on `<html>` after the idle threshold
 * elapses (default 30s). Reverts to no attribute the moment any input
 * event fires (handled by `useIdleState`).
 *
 * Why a data-attribute on :root, not a context: any component anywhere
 * in the tree can opt in via CSS without prop drilling, e.g.:
 *
 *   :root[data-life-idle="true"] .barrier-constellation {
 *     animation-duration: 12s; // baseline 18s — speed up subtly
 *   }
 *   :root[data-life-idle="true"] .path-line-header {
 *     animation: path-pulse 2s ease-in-out infinite;
 *   }
 *
 * The provider renders nothing visible — pure side-effect. Mounted by
 * WallContainer alongside AccentTokenProvider so the attribute is
 * available before chapter components paint.
 *
 * Reduced-motion: the attribute STILL sets. Consumer CSS is responsible
 * for ignoring it under `@media (prefers-reduced-motion: reduce)`.
 */

import { useEffect } from "react";
import { useIdleState } from "@/hooks/useIdleState";

const ATTR_NAME = "data-life-idle";

interface IdleStateProviderProps {
  /** Inactivity threshold in milliseconds. Default 30 000. */
  idleMs?: number;
}

export function IdleStateProvider({
  idleMs = 30_000,
}: IdleStateProviderProps = {}): null {
  const idle = useIdleState(idleMs);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    if (idle) {
      root.setAttribute(ATTR_NAME, "true");
    } else {
      root.removeAttribute(ATTR_NAME);
    }
    return () => {
      // Cleanup on unmount: never leave a stale attribute on :root.
      root.removeAttribute(ATTR_NAME);
    };
  }, [idle]);

  return null;
}
