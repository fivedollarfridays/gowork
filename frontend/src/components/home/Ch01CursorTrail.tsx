"use client";

/**
 * Ch01CursorTrail — polish-2 T48.
 *
 * 12-particle amber trail with a 600ms decay, constrained to `.ch01`.
 * Distinct from `CursorFlashlight` (radial glow) and the wall-tier
 * `CursorTrail` (single cyan dot lag). This one is a particle wake.
 *
 * Disabled when:
 *   - `prefers-reduced-motion: reduce` is on
 *   - the pointer is coarse (touch — `(pointer: coarse)` matches OR
 *     `navigator.maxTouchPoints > 0`)
 *
 * Constrained to Ch1 by attaching the listener to `.ch01` directly when
 * available; on document-level pointermove, the helper checks the
 * event's `target.closest(".ch01")` so a particle is only spawned when
 * the cursor is inside the chapter.
 *
 * Particle pool: 12 max. Each particle is a `<span data-trail>` that
 * starts at the pointer position and decays to opacity 0 over 600ms via
 * the CSS rule in `home-velocity.css` (data-trail[data-decay="true"]).
 * After decay we DOM-remove the node so the pool stays small.
 */
import { useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

const PARTICLE_LIMIT = 12;
const DECAY_MS = 600;

function detectCoarse(): boolean {
  if (typeof window === "undefined") return false;
  if (typeof navigator !== "undefined" && (navigator.maxTouchPoints ?? 0) > 0) {
    return true;
  }
  if (typeof window.matchMedia === "function") {
    if (window.matchMedia("(pointer: coarse)").matches) return true;
  }
  return false;
}

export function Ch01CursorTrail(): JSX.Element | null {
  const reduced = usePrefersReducedMotion();
  const [coarse, setCoarse] = useState<boolean>(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  // Pool of currently-active particle nodes — used to enforce the cap.
  const poolRef = useRef<HTMLSpanElement[]>([]);

  useEffect(() => {
    setCoarse(detectCoarse());
  }, []);

  useEffect(() => {
    if (reduced || coarse) return;
    if (typeof document === "undefined") return;
    const root = rootRef.current;
    if (!root) return;

    const onPointerMove = (e: PointerEvent) => {
      const target = e.target as Element | null;
      // Only fire when the cursor is inside .ch01.
      if (!target || !target.closest?.(".ch01")) return;
      spawnParticle(root, poolRef.current, e.clientX, e.clientY);
    };

    document.addEventListener("pointermove", onPointerMove, { passive: true });
    return () => document.removeEventListener("pointermove", onPointerMove);
  }, [reduced, coarse]);

  if (reduced || coarse) return null;
  return (
    <div
      ref={rootRef}
      data-ch01-trail-root
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        pointerEvents: "none",
        zIndex: 1,
      }}
    />
  );
}

function spawnParticle(
  root: HTMLDivElement,
  pool: HTMLSpanElement[],
  x: number,
  y: number,
): void {
  // Cap the pool. Drop the oldest if we're at the limit.
  while (pool.length >= PARTICLE_LIMIT) {
    const oldest = pool.shift();
    if (oldest && oldest.parentNode) oldest.parentNode.removeChild(oldest);
  }
  const particle = document.createElement("span");
  particle.setAttribute("data-trail", "");
  particle.style.left = `${x}px`;
  particle.style.top = `${y}px`;
  particle.style.transform = "translate3d(-50%, -50%, 0)";
  root.appendChild(particle);
  pool.push(particle);
  // Trigger decay on the next frame so the CSS transition runs.
  if (typeof requestAnimationFrame === "function") {
    requestAnimationFrame(() => {
      particle.setAttribute("data-decay", "true");
    });
  } else {
    particle.setAttribute("data-decay", "true");
  }
  // Remove after the decay window.
  setTimeout(() => {
    if (particle.parentNode) particle.parentNode.removeChild(particle);
    const idx = pool.indexOf(particle);
    if (idx >= 0) pool.splice(idx, 1);
  }, DECAY_MS + 80);
}
