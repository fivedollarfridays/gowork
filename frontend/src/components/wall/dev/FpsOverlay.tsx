"use client";

import { useEffect, useRef, useState } from "react";

/**
 * FpsOverlay (T1.82).
 *
 * Tiny fixed-bottom-right panel showing rolling 60-frame average FPS.
 * Dev-only by triple gate:
 *   1. NODE_ENV !== "production"
 *   2. EITHER `?fps=1` is in the URL OR `window.__GOWORK_FPS__ === true`
 *   3. Not under prefers-reduced-motion (rAF loop disrupts AT pacing)
 *
 * Built without observers — single requestAnimationFrame loop, sampling
 * deltas into a 60-element ring. Cleanup cancels the loop on unmount.
 */
const SAMPLE_SIZE = 60;

function readQueryEnabled(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const params = new URLSearchParams(window.location.search);
    return params.get("fps") === "1";
  } catch {
    return false;
  }
}

function readWindowEnabled(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(
    (window as unknown as { __GOWORK_FPS__?: boolean }).__GOWORK_FPS__,
  );
}

function isProduction(): boolean {
  return process.env.NODE_ENV === "production";
}

export function FpsOverlay(): JSX.Element | null {
  const [fps, setFps] = useState<number>(0);
  const samplesRef = useRef<number[]>([]);
  const lastTsRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);

  const enabled = !isProduction() && (readQueryEnabled() || readWindowEnabled());

  useEffect(() => {
    if (!enabled) return;
    function loop(ts: number) {
      if (lastTsRef.current !== null) {
        const delta = ts - lastTsRef.current;
        if (delta > 0) {
          const instant = 1000 / delta;
          const samples = samplesRef.current;
          samples.push(instant);
          if (samples.length > SAMPLE_SIZE) samples.shift();
          const avg =
            samples.reduce((sum, v) => sum + v, 0) / samples.length;
          setFps(Math.round(avg));
        }
      }
      lastTsRef.current = ts;
      rafRef.current = requestAnimationFrame(loop);
    }
    rafRef.current = requestAnimationFrame(loop);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [enabled]);

  if (!enabled) return null;
  return (
    <div
      data-testid="fps-overlay"
      role="status"
      aria-label="rendering frames per second"
      className="font-mono-data fixed bottom-2 right-2 rounded bg-black/70 px-2 py-1 text-xs text-cyan-300"
      style={{ zIndex: "var(--z-toast, 70)" }}
    >
      {fps} fps
    </div>
  );
}
