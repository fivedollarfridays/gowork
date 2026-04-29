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
 *
 * NOTE: Driver A is the canonical implementer. Other drivers consume this
 * hook via import. If you arrive here before Driver A's commit lands, fill
 * the body — but keep the public signature stable.
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

export function useMagneticHover<T extends HTMLElement = HTMLElement>(
  _opts: MagneticHoverOptions = {},
): React.RefObject<T> {
  const ref = useRef<T>(null);

  useEffect(() => {
    // SCAFFOLD: real implementation lands in Driver A's polish-2 commit.
    // Until then, the hook is a no-op so consuming components don't break.
    return undefined;
  }, []);

  return ref;
}
