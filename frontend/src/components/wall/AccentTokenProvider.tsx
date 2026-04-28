"use client";

import { useEffect } from "react";
import { useTimeOfDay } from "@/hooks/useTimeOfDay";
import type { AccentToken } from "@/lib/wall/timeOfDayPalette";

/**
 * T4.A.2 — AccentTokenProvider.
 *
 * Sets `--accent-current` on `:root` (the document element) keyed to
 * the current time-of-day phase. Additive only: never touches existing
 * tokens. Chapter accent backgrounds + the press kit OG card share this
 * variable.
 *
 * The component renders nothing — it's a pure side-effect provider so
 * mounting order is flexible (anywhere inside the tree works; we mount
 * at WallContainer level so the value is set before chapters paint).
 *
 * Reduced-motion contract: the variable still updates because chapter
 * accent fills are static colours, not animations. Reduced-motion only
 * affects the rate of phase ticks (which `useTimeOfDay` already throttles
 * to once-per-minute regardless).
 */

/** Token → OKLCH map shared with `timeOfDayPalette`. We store the OKLCH
 *  on the CSS custom prop directly so consumers can `var(--accent-current)`
 *  without an additional indirection layer. */
const ACCENT_TOKEN_TO_OKLCH: Record<AccentToken, string> = {
  amber: "oklch(0.78 0.13 70)",
  cyan: "oklch(0.78 0.12 200)",
  blue: "oklch(0.65 0.16 250)",
  rose: "oklch(0.68 0.18 15)",
  indigo: "oklch(0.45 0.15 280)",
};

export function AccentTokenProvider(): null {
  const { accentToken } = useTimeOfDay();

  useEffect(() => {
    if (typeof document === "undefined") return;
    const value = ACCENT_TOKEN_TO_OKLCH[accentToken] ?? ACCENT_TOKEN_TO_OKLCH.blue;
    document.documentElement.style.setProperty("--accent-current", value);
    return () => {
      // Leave the value set on unmount — pages without the wall (e.g.,
      // /jobs) still benefit from a sensible default. We only clear in
      // tests via the manual cleanup in beforeEach/afterEach.
    };
  }, [accentToken]);

  return null;
}
