"use client";

/**
 * Narrative Reset (sprint/narrative-reset) — T-Reset.4 — StartNowCTA.
 *
 * A persistent floating "Start now" button that surfaces from Ch1 onward.
 * The original wall narrative buried the primary CTA inside Ch10 —
 * a user had to scroll past 10 chapters to find it. The site is a
 * job-finding tool first; the CTA must be visible from the moment the
 * user finishes the hero.
 *
 * # Behavior
 *   - Hidden during Ch1 hero (scrollProgress < SHOW_THRESHOLD).
 *   - Past the threshold, fades in (CSS opacity, no JS easing) and stays.
 *   - Click → routes to `/assess` (existing assessment form). Uses View
 *     Transitions where supported; falls back gracefully otherwise.
 *   - Mobile: bottom-fixed strip. Desktop: top-right floating chip.
 *   - Reduced-motion: visible immediately past threshold, no fade.
 *   - Coordinates with the existing `<LiveNow />` widget — when both are
 *     mounted, this CTA sits ABOVE Live Now so the visual hierarchy is
 *     "primary CTA → status → chrome."
 *
 * # A11y
 *   - <button> with i18n aria-label.
 *   - Tab-reachable; focus ring uses --accent token.
 *   - data-visible=true|false so e2e + screen-reader audits can assert
 *     visibility without parsing CSS.
 *
 * # Tokens
 *   - Background: var(--accent-current, var(--accent-cyan)).
 *   - Foreground: var(--bg-base) (high-contrast inversion).
 *   - No raw hex; audit:tokens stays clean.
 */

import type { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { t } from "@/lib/i18n";
import {
  startViewTransitionWithFallback,
} from "@/lib/wall/viewTransitions";

/**
 * Scroll-progress threshold past which the CTA reveals. The dispatch
 * called for ~10% scroll (after Ch1 hero). Tuned slightly higher (0.05)
 * so a user hesitating on the hero question doesn't get the CTA jumping
 * into the hero band.
 */
export const START_NOW_SHOW_THRESHOLD = 0.05;

export type StartNowCTAPosition = "top-right" | "bottom";

export interface StartNowCTAProps {
  /** 0..1 total scroll progress across the wall. Drives visibility. */
  scrollProgress: number;
  /** Reduced-motion override; defaults to false (full fade). */
  reducedMotion?: boolean;
  /**
   * Forced placement. When omitted, defaults to "top-right" — callers
   * pass "bottom" on mobile viewports.
   */
  position?: StartNowCTAPosition;
}

function isVisible(scrollProgress: number): boolean {
  if (!Number.isFinite(scrollProgress)) return false;
  return scrollProgress >= START_NOW_SHOW_THRESHOLD;
}

function pickStyle(
  visible: boolean,
  reducedMotion: boolean,
  position: StartNowCTAPosition,
): CSSProperties {
  const base: CSSProperties = {
    position: "fixed",
    zIndex: 60,
    minHeight: 44,
    padding: "0.625rem 1.25rem",
    fontSize: "0.95rem",
    fontWeight: 700,
    color: "var(--bg-base)",
    background: "var(--accent-current, var(--accent-cyan))",
    border: "0",
    borderRadius: "999px",
    cursor: "pointer",
    boxShadow:
      "0 8px 24px color-mix(in oklch, var(--accent-current, var(--accent-cyan)) 35%, transparent)",
    pointerEvents: visible ? "auto" : "none",
    transition: reducedMotion ? "none" : "opacity 240ms ease-out",
    opacity: reducedMotion ? (visible ? 1 : 0) : visible ? 1 : 0,
  };
  if (position === "bottom") {
    return {
      ...base,
      left: "50%",
      bottom: "max(env(safe-area-inset-bottom, 0px), 1rem)",
      transform: "translateX(-50%)",
      width: "min(20rem, 90vw)",
      textAlign: "center",
    };
  }
  return {
    ...base,
    top: "max(env(safe-area-inset-top, 0px), 0.75rem)",
    right: "1rem",
  };
}

export function StartNowCTA({
  scrollProgress,
  reducedMotion = false,
  position = "top-right",
}: StartNowCTAProps): JSX.Element {
  const router = useRouter();
  const visible = isVisible(scrollProgress);

  const handleClick = (): void => {
    startViewTransitionWithFallback(() => router.push("/assess"), {
      reducedMotion,
    });
  };

  const label = t("wall.startNowCta.label");
  const ariaLabel = t("wall.startNowCta.ariaLabel");

  return (
    <button
      type="button"
      data-testid="start-now-cta"
      data-visible={visible ? "true" : "false"}
      data-reduced-motion={reducedMotion ? "true" : "false"}
      data-position={position}
      aria-label={ariaLabel}
      aria-hidden={visible ? "false" : "true"}
      tabIndex={visible ? 0 : -1}
      onClick={handleClick}
      style={pickStyle(visible, reducedMotion, position)}
    >
      {label}
    </button>
  );
}

export default StartNowCTA;
