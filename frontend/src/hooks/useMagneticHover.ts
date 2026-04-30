"use client";

/**
 * useMagneticHover — polish-2 T1 / T28 / T37.
 *
 * Pull a target element toward the cursor when it enters a configurable
 * proximity radius. Used on Ch1 hero primary CTA (T1), Ch6 JobCard apply
 * CTAs (T28), and the idle-orbit fallback on Ch1 CTA (T37).
 *
 * Contract:
 *   const ref = useMagneticHover<HTMLAnchorElement>({ disabled });
 *   <Link ref={ref} ... />
 *
 * Behavior:
 *   - Reads `--magnetic-pull-distance` (default 80px) and
 *     `--magnetic-pull-max` (default 10px) from CSS custom properties so
 *     designers can re-tune without code changes.
 *   - Skips the effect when `disabled` is true OR when the user prefers
 *     reduced motion OR when `(pointer: coarse)` matches.
 *   - Uses requestAnimationFrame easing (lerp 0.18) so the pull feels like
 *     a soft spring rather than a 1:1 follow.
 *   - Cleans up on unmount (no leaked rAF / listeners).
 */

import { useEffect, useRef } from "react";

export interface MagneticHoverOptions {
  /** Disable the effect entirely (e.g. when a parent pre-empts it). */
  disabled?: boolean;
  /** Override the proximity radius in px (defaults to CSS token). */
  distance?: number;
  /** Override the max pull translation in px (defaults to CSS token). */
  maxPull?: number;
}

const DEFAULT_DISTANCE = 80;
const DEFAULT_MAX_PULL = 10;
const LERP = 0.18;
const REST_EPS = 0.05;

function readNumberToken(name: string, fallback: number): number {
  if (typeof window === "undefined" || typeof getComputedStyle !== "function") {
    return fallback;
  }
  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  if (!raw) return fallback;
  const n = parseFloat(raw);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function isCoarsePointer(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(pointer: coarse)").matches;
}

function isReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function useMagneticHover<T extends HTMLElement = HTMLElement>(
  opts: MagneticHoverOptions = {},
): React.RefObject<T> {
  const ref = useRef<T>(null);
  const { disabled = false, distance, maxPull } = opts;

  useEffect(() => {
    if (disabled || typeof window === "undefined") return undefined;
    if (isCoarsePointer() || isReducedMotion()) return undefined;

    const proximity = distance ?? readNumberToken("--magnetic-pull-distance", DEFAULT_DISTANCE);
    const cap = maxPull ?? readNumberToken("--magnetic-pull-max", DEFAULT_MAX_PULL);

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let rafId: number | null = null;
    let scheduled = false;

    const apply = () => {
      const el = ref.current;
      if (!el) {
        scheduled = false;
        return;
      }
      currentX += (targetX - currentX) * LERP;
      currentY += (targetY - currentY) * LERP;
      el.style.transform = `translate3d(${currentX.toFixed(3)}px, ${currentY.toFixed(3)}px, 0)`;
      const dx = targetX - currentX;
      const dy = targetY - currentY;
      if (Math.abs(dx) < REST_EPS && Math.abs(dy) < REST_EPS && targetX === 0 && targetY === 0) {
        // Snap to rest and stop the rAF chain.
        currentX = 0;
        currentY = 0;
        el.style.transform = `translate3d(0px, 0px, 0)`;
        scheduled = false;
        rafId = null;
        return;
      }
      rafId = window.requestAnimationFrame(apply);
    };

    const schedule = () => {
      if (scheduled) return;
      scheduled = true;
      rafId = window.requestAnimationFrame(apply);
    };

    const onMove = (event: MouseEvent) => {
      const el = ref.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = event.clientX - cx;
      const dy = event.clientY - cy;
      const dist = Math.hypot(dx, dy);
      if (dist > proximity) {
        targetX = 0;
        targetY = 0;
      } else {
        // Pull strength scales linearly with proximity (1 at center → 0 at radius).
        const strength = 1 - dist / proximity;
        targetX = Math.max(-cap, Math.min(cap, dx * strength * 0.35));
        targetY = Math.max(-cap, Math.min(cap, dy * strength * 0.35));
      }
      schedule();
    };

    const onLeave = () => {
      targetX = 0;
      targetY = 0;
      schedule();
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    window.addEventListener("mouseleave", onLeave);
    const el = ref.current;
    el?.addEventListener("pointerleave", onLeave);

    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseleave", onLeave);
      el?.removeEventListener("pointerleave", onLeave);
      if (rafId !== null) {
        window.cancelAnimationFrame(rafId);
      }
      if (el) {
        el.style.transform = "";
      }
    };
  }, [disabled, distance, maxPull]);

  return ref;
}
