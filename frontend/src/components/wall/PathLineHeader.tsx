"use client";

import { useEffect, useState } from "react";

/**
 * T1.50 — Persistent path-line header.
 *
 * Renders a 2px cyan line stuck to the top edge of the viewport that
 * draws from 0% to 100% width as the page scrolls from top to bottom.
 * The path is the literal embodiment of the route metaphor and stays
 * visible across every chapter so the user always knows where they are.
 *
 * The progress is normalized 0..1 and passed in by the consumer. Driver
 * B's `useScrollProgress` hook (W2 / not yet merged at W1 time) wires
 * window scroll into a motion value and feeds this component. Until
 * then, the component supports a fallback path : if no progress is
 * provided (undefined), it self-subscribes to window scroll.
 *
 * Reduced-motion : when true, the line is rendered fully filled — the
 * indicator is still useful as orientation, it just stops animating.
 */
export interface PathLineHeaderProps {
  /** Normalized scroll progress 0..1. If omitted, the component
   *  self-subscribes to window scroll. */
  progress?: number;
  /** When true, force 100% fill (skip motion). Driver A's globals.css
   *  may also gate this via the prefers-reduced-motion media query. */
  reducedMotion?: boolean;
}

function clamp01(n: number): number {
  if (Number.isNaN(n)) return 0;
  if (n < 0) return 0;
  if (n > 1) return 1;
  return n;
}

function useSelfScrollProgress(active: boolean): number {
  const [p, setP] = useState(0);
  useEffect(() => {
    if (!active || typeof window === "undefined") return;
    function recompute() {
      const max =
        document.documentElement.scrollHeight - window.innerHeight;
      const ratio = max > 0 ? window.scrollY / max : 0;
      setP(clamp01(ratio));
    }
    recompute();
    window.addEventListener("scroll", recompute, { passive: true });
    window.addEventListener("resize", recompute);
    return () => {
      window.removeEventListener("scroll", recompute);
      window.removeEventListener("resize", recompute);
    };
  }, [active]);
  return p;
}

export function PathLineHeader({
  progress,
  reducedMotion = false,
}: PathLineHeaderProps): JSX.Element {
  const selfProgress = useSelfScrollProgress(progress === undefined);
  const value = clamp01(progress ?? selfProgress);
  const widthPct = reducedMotion ? 100 : value * 100;
  return (
    <div
      data-path-line
      aria-hidden="true"
      className="pointer-events-none fixed inset-x-0 top-0 z-[60] h-0.5 bg-foreground/5"
    >
      <div
        data-path-line-fill
        className="h-full bg-cyan-400 transition-[width] duration-150 ease-out"
        style={{ width: `${widthPct}%` }}
      />
    </div>
  );
}
