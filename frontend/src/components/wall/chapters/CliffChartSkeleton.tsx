"use client";

/**
 * W3 Driver D Spotlight invention — CliffChartSkeleton.
 *
 * Renders a lightweight placeholder that mimics the BenefitsCliffChart
 * bounding box while Recharts hydrates via next/dynamic. Without this,
 * lazy-loading the chart would cause a layout shift the moment Recharts
 * arrives — a visible jump that betrays the "one product" feel.
 *
 * # Why a hand-built SVG instead of a Tailwind shimmer
 *
 * The skeleton exists for layout stability + cinematic continuity, not
 * "loading bling." A 320px-tall card with a striped cliff zone (matching
 * the real chart's reference markers) tells the user "the cliff is being
 * drawn" without being a cosmetic distraction.
 *
 * # Spotlight Lens — Structural
 *
 * Bundle budget recovery is not just code-size; it's perceptual quality.
 * The skeleton turns a regression-prevention chore into a polish moment:
 * the user sees the chart's silhouette before the chart arrives. Same
 * bounding box, same cliff hint, same temperature-aware tint via the
 * existing --accent-current token.
 */
import type { ReactElement } from "react";

export function CliffChartSkeleton(): ReactElement {
  return (
    <div
      data-testid="ch6-cliff-chart-skeleton"
      role="img"
      aria-label="Loading benefits cliff chart"
      className="rounded-lg border"
      style={{
        height: 380,
        width: "100%",
        background: "color-mix(in oklch, var(--bg-base) 92%, transparent)",
        borderColor: "color-mix(in oklch, var(--accent-current) 25%, transparent)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <span
        className="absolute left-4 top-3 text-sm font-medium opacity-70"
        style={{ color: "var(--fg-secondary, var(--fg-primary))" }}
      >
        Net Income vs. Hourly Wage
      </span>
      <svg
        viewBox="0 0 320 200"
        width="100%"
        height="100%"
        preserveAspectRatio="none"
        focusable="false"
        aria-hidden="true"
        style={{ marginTop: 24 }}
      >
        {/* Cliff zone stripe — hints where the real chart's cliff bar lands. */}
        <defs>
          <pattern
            id="cliff-skeleton-stripe"
            width={8}
            height={8}
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(45)"
          >
            <line
              x1={0}
              y1={0}
              x2={0}
              y2={8}
              stroke="var(--accent-current)"
              strokeWidth={2}
              opacity={0.4}
            />
          </pattern>
        </defs>
        <rect
          x={185}
          y={20}
          width={50}
          height={160}
          fill="url(#cliff-skeleton-stripe)"
          opacity={0.5}
        />
        {/* Faded baseline — where the cliff curve will dip. */}
        <path
          d="M 10 60 L 80 60 L 130 70 L 175 95 L 210 150 L 260 145 L 310 145"
          fill="none"
          stroke="var(--accent-current)"
          strokeWidth={2}
          strokeOpacity={0.4}
          strokeDasharray="6 4"
        />
      </svg>
    </div>
  );
}

export default CliffChartSkeleton;
