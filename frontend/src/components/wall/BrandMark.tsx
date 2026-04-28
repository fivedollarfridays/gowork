"use client";

/**
 * BrandMark — inline copy of public/icon.svg.
 *
 * The on-disk icon.svg is the SOURCE of truth for the favicon /
 * social raster pipeline (see scripts/generate-brand-rasters.mjs).
 * For React composition (Header, Footer, edge states), inline the
 * same geometry so we get fill + size control + hover transitions
 * without an extra image fetch.
 *
 * Geometry mirrors the on-disk file : 16-coordinate viewBox, 270°
 * G arc with stroke-width 2.4, horizontal cyan #22D3EE path-line
 * extending to x=15 (past the right edge). Designed at 16px first.
 */
export interface BrandMarkProps {
  /** Square pixel size. Defaults to 24. */
  size?: number;
  /** Optional class for layout / hover styling. */
  className?: string;
  /** Whether the cyan path-line should be visible (default true). */
  showPath?: boolean;
}

export function BrandMark({
  size = 24,
  className = "",
  showPath = true,
}: BrandMarkProps): JSX.Element {
  return (
    <svg
      role="img"
      aria-label="GoWork"
      width={size}
      height={size}
      viewBox="0 0 16 16"
      className={`gowork-mark ${className}`}
    >
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth={2.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M 14 8 A 6 6 0 1 0 8 14" />
      </g>
      {showPath ? (
        <line
          x1={8}
          y1={8}
          x2={15}
          y2={8}
          stroke="#22D3EE"
          strokeWidth={2.4}
          strokeLinecap="round"
          className="gowork-mark__path"
        />
      ) : null}
    </svg>
  );
}
