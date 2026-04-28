"use client";

/**
 * Chapter 01 — Continental (T2.19, T2.20, T2.21, T2.22).
 *
 * Top-down America at zoom 3. Editorial overlay locks the hero question
 * and subhero copy from `docs/visual-rebirth-plan.md` (do not redraft).
 * The variable font axis interpolates 700→900 across chapter progress
 * (W1 `useVariableFontWeight`).
 *
 * # Driver-coordination
 *
 * This chapter is **scaffold-agnostic** — it accepts a `progress` prop
 * (0..1 within-chapter) so Driver A's WallContainer + ChapterScaffold
 * can wrap it when merged without refactoring this file. The component
 * owns its own overlay markup; ChapterScaffold provides sticky pinning
 * + atmosphere shell.
 *
 * # Reduced-motion contract
 *
 * - Variable font weight locks at the W1 fallback (800/23) when
 *   `prefers-reduced-motion: reduce` is on (delegated to the hook).
 * - Overlay opacity is constant 1 in reduced-motion (data-fallback hook
 *   for visual-regression assertions).
 *
 * # WCAG AAA contrast
 *
 * Heading + body use W1 `--fg-primary` on a `--bg-base/0` glass layer
 * — token-driven; no hardcoded colors.
 */

import { useVariableFontWeight } from "@/hooks/useVariableFontWeight";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useTranslation } from "@/hooks/useTranslation";

export interface Chapter01ContinentalProps {
  /** 0..1 progress within Chapter 1's scroll range (Driver A wires). */
  progress: number;
  /** Optional override for the chapter id used in data attributes. */
  chapterId?: string;
}

export function Chapter01Continental({
  progress,
  chapterId = "continental",
}: Chapter01ContinentalProps) {
  const reduced = usePrefersReducedMotion();
  const fontVariation = useVariableFontWeight(progress);
  const { t } = useTranslation();

  // Static-fallback flag: when reduced-motion is on, the overlay is at
  // full opacity from the start (no scroll-tied fade).
  const fallback = reduced ? "static" : "scroll";

  return (
    <section
      data-testid="ch1-section"
      data-chapter-id={chapterId}
      aria-labelledby="ch1-heading"
      style={{
        position: "relative",
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
      }}
    >
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        style={{
          position: "absolute",
          width: 1,
          height: 1,
          margin: -1,
          padding: 0,
          overflow: "hidden",
          clip: "rect(0 0 0 0)",
          whiteSpace: "nowrap",
          border: 0,
        }}
      >
        {t("wall.ch1.ariaLive")}
      </div>

      <div
        data-testid="ch1-overlay"
        data-fallback={fallback}
        style={{
          maxWidth: "48rem",
          padding: "2rem",
          textAlign: "center",
          color: "var(--fg-primary)",
          background: "color-mix(in oklch, var(--bg-base) 60%, transparent)",
          borderRadius: "var(--radius)",
          backdropFilter: "blur(8px)",
          opacity: reduced ? 1 : Math.max(0.85, progress),
          transition: reduced ? "none" : "opacity 200ms ease-out",
        }}
      >
        <h1
          id="ch1-heading"
          style={{
            fontFamily: "var(--font-inter-stack)",
            fontSize: "clamp(2.5rem, 6vw, 5rem)",
            letterSpacing: "-0.04em",
            lineHeight: 1.05,
            margin: 0,
            color: "var(--fg-primary)",
            fontVariationSettings: fontVariation,
          }}
        >
          {t("wall.ch1.hero")}
        </h1>
        <p
          style={{
            marginTop: "1.5rem",
            fontSize: "1.125rem",
            lineHeight: 1.55,
            color: "var(--fg-secondary, var(--fg-primary))",
          }}
        >
          {t("wall.ch1.subhero")}
        </p>
      </div>
    </section>
  );
}
