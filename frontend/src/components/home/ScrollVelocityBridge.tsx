"use client";

/**
 * ScrollVelocityBridge — polish-2 T56 / T57 / T59.
 *
 * One stateless component, three body-level data attributes:
 *
 *   - T56 `data-scroll-velocity="fast"` when `useScrollVelocity().isFast`
 *     is true. CSS rule (home-velocity.css) applies a soft motion-blur
 *     filter to chapter content while flipping. Removes when slow.
 *
 *   - T57 `data-battery-low` when `useBatteryAware().isLow` is true
 *     (battery < 20% AND not charging). CSS rule disables expensive
 *     animations and the cursor flashlight for the low-battery user.
 *
 *   - T59 `data-idle="true"` when `useIdleState(8000)` is true. CSS rule
 *     gives Ch4 markers a 1px ambient orbit — the city stays alive
 *     while the user is reading.
 *
 * The bridge renders nothing; it only writes/removes body attrs in
 * effects. Cleanup on unmount removes every attr — important for tests
 * sharing the same `document.body`.
 */
import { useEffect } from "react";
import { useScrollVelocity } from "@/hooks/useScrollVelocity";
import { useBatteryAware } from "@/hooks/useBatteryAware";
import { useIdleState } from "@/hooks/useIdleState";

const FAST_SCROLL_PX_PER_MS = 0.8; // ≈ 800 px / s

const IDLE_AMBIENT_MS = 8000;

export function ScrollVelocityBridge(): null {
  const { isFast } = useScrollVelocity(FAST_SCROLL_PX_PER_MS);
  const battery = useBatteryAware();
  const idle = useIdleState(IDLE_AMBIENT_MS);

  useEffect(() => {
    if (typeof document === "undefined") return;
    if (isFast) {
      document.body.setAttribute("data-scroll-velocity", "fast");
    } else {
      document.body.removeAttribute("data-scroll-velocity");
    }
  }, [isFast]);

  useEffect(() => {
    if (typeof document === "undefined") return;
    if (battery.isLow) {
      document.body.setAttribute("data-battery-low", "");
    } else {
      document.body.removeAttribute("data-battery-low");
    }
  }, [battery.isLow]);

  useEffect(() => {
    if (typeof document === "undefined") return;
    if (idle) {
      document.body.setAttribute("data-idle", "true");
    } else {
      document.body.removeAttribute("data-idle");
    }
  }, [idle]);

  // Final cleanup on unmount — covers tests that mount/unmount in a tight
  // loop and rely on a clean body for the next assertion.
  useEffect(() => {
    return () => {
      if (typeof document === "undefined") return;
      document.body.removeAttribute("data-scroll-velocity");
      document.body.removeAttribute("data-battery-low");
      document.body.removeAttribute("data-idle");
    };
  }, []);

  return null;
}
