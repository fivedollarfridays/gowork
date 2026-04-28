"use client";

import { useEffect, useState } from "react";

/** Viewport-based responsive tier. */
export type ResponsiveTier = "mobile" | "tablet" | "desktop";

/** Lower boundary of the tablet tier (matches Tailwind's `md` breakpoint). */
export const TABLET_MIN_WIDTH = 768;
/** Lower boundary of the desktop tier (matches Tailwind's `lg` breakpoint). */
export const DESKTOP_MIN_WIDTH = 1024;

export interface ResponsiveTierState {
  tier: ResponsiveTier;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  /** Current `window.innerWidth`. Useful for bespoke breakpoint logic. */
  width: number;
}

const SSR_DEFAULT: ResponsiveTierState = {
  tier: "desktop",
  isMobile: false,
  isTablet: false,
  isDesktop: true,
  width: DESKTOP_MIN_WIDTH,
};

function classify(width: number): ResponsiveTier {
  if (width < TABLET_MIN_WIDTH) return "mobile";
  if (width < DESKTOP_MIN_WIDTH) return "tablet";
  return "desktop";
}

function readState(): ResponsiveTierState {
  if (typeof window === "undefined") return SSR_DEFAULT;
  const width = window.innerWidth;
  const tier = classify(width);
  return {
    tier,
    isMobile: tier === "mobile",
    isTablet: tier === "tablet",
    isDesktop: tier === "desktop",
    width,
  };
}

/**
 * Viewport-based responsive tier hook.
 *
 * Returns `mobile` (<768), `tablet` (768-1023), or `desktop` (≥1024).
 * Subscribes to `window.resize` so rotation / drawer-open re-tier the UI
 * without a full reload.
 *
 * SSR-safe: returns 'desktop' on the server to avoid hydration mismatch
 * for the most common case (judges scouting on laptops). Mobile users
 * see the correct tier on the first useEffect tick.
 *
 * Why this lives outside `useDeviceCapability`: hardware capability
 * (memory, cores, save-data) is orthogonal to viewport tier. A high-end
 * phone has high `tier` in `useDeviceCapability` but `mobile` here.
 */
export function useResponsiveTier(): ResponsiveTierState {
  const [state, setState] = useState<ResponsiveTierState>(SSR_DEFAULT);

  useEffect(() => {
    setState(readState());
    function onResize() {
      setState(readState());
    }
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return state;
}
