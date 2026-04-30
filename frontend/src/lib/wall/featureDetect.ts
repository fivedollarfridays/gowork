/**
 * Centralized feature-detect (Spotlight invention).
 *
 * Wraps the assorted `'API' in window`, `CSS.supports()`, and
 * `document.startViewTransition` checks the wall scatters across
 * components into one module. Each probe is pure + SSR-safe (returns
 * false when window/CSS is undefined).
 *
 * Use sparingly — many CSS features have @supports + graceful degradation
 * built in. This module is for the cases where JS branches on the
 * detection (e.g., decide whether to run a View Transitions choreography
 * or a fallback fade).
 */

function hasWindow(): boolean {
  return typeof window !== "undefined";
}

function hasCSS(): boolean {
  return typeof CSS !== "undefined" && typeof CSS.supports === "function";
}

export function hasViewTransitions(): boolean {
  if (!hasWindow()) return false;
  return typeof (document as unknown as { startViewTransition?: unknown })
    .startViewTransition === "function";
}

export function hasContainerQueries(): boolean {
  if (!hasCSS()) return false;
  try {
    return CSS.supports("container-type: inline-size");
  } catch {
    return false;
  }
}

export function hasColorMix(): boolean {
  if (!hasCSS()) return false;
  try {
    return CSS.supports("color: color-mix(in oklch, white, black)");
  } catch {
    return false;
  }
}

export function hasOklch(): boolean {
  if (!hasCSS()) return false;
  try {
    return CSS.supports("color: oklch(50% 0 0)");
  } catch {
    return false;
  }
}

export function hasVibration(): boolean {
  if (!hasWindow()) return false;
  return typeof navigator !== "undefined" && typeof navigator.vibrate === "function";
}

export function hasBatteryAPI(): boolean {
  if (!hasWindow()) return false;
  const nav = navigator as unknown as { getBattery?: () => Promise<unknown> };
  return typeof nav.getBattery === "function";
}

export interface FeatureFlags {
  viewTransitions: boolean;
  containerQueries: boolean;
  colorMix: boolean;
  oklch: boolean;
  vibration: boolean;
  batteryAPI: boolean;
}

export function detectFeatures(): FeatureFlags {
  return {
    viewTransitions: hasViewTransitions(),
    containerQueries: hasContainerQueries(),
    colorMix: hasColorMix(),
    oklch: hasOklch(),
    vibration: hasVibration(),
    batteryAPI: hasBatteryAPI(),
  };
}
