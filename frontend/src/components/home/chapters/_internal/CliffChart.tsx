"use client";

/**
 * Cliff chart SVG for Chapter 07.
 *
 * Renders the dramatic dip + recovery curve. Marker position is supplied by
 * the parent (drives off the slider value via `computeCliff`).
 *
 * polish-2 T31 — adds two hoverable annotations:
 *   - cliff edge ($19) — explains SNAP cuts + childcare voucher lapse.
 *   - destination ($22.50) — labels the Alcon production-tech wage as the
 *     job the whole map orbits around.
 *
 * Pulled into its own component to keep the parent under arch limits.
 */

import { useState, type ReactElement } from "react";

interface CliffChartProps {
  markerX: number;
  markerY: number;
  ariaLabel: string;
  cliffZoneLabel: string;
  tooltipCliff: string;
  tooltipDestination: string;
}

type AnnotationKey = "cliff" | "destination";

export function CliffChart({
  markerX,
  markerY,
  ariaLabel,
  cliffZoneLabel,
  tooltipCliff,
  tooltipDestination,
}: CliffChartProps): ReactElement {
  const [hovered, setHovered] = useState<AnnotationKey | null>(null);
  const tipText =
    hovered === "cliff"
      ? tooltipCliff
      : hovered === "destination"
      ? tooltipDestination
      : null;

  return (
    <div style={{ position: "relative" }}>
      <svg
        viewBox="0 0 600 420"
        role="img"
        aria-label={ariaLabel}
        style={{ width: "100%", height: "auto" }}
      >
        <defs>
          <linearGradient id="cliff-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FB7185" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#FB7185" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="cliff-up" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#34D399" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#34D399" stopOpacity="0" />
          </linearGradient>
        </defs>

        <g className="grid">
          <line x1="60" y1="60" x2="580" y2="60" />
          <line x1="60" y1="140" x2="580" y2="140" />
          <line x1="60" y1="220" x2="580" y2="220" />
          <line x1="60" y1="300" x2="580" y2="300" />
          <line x1="60" y1="380" x2="580" y2="380" />
        </g>

        <g className="ylab">
          <text x="50" y="64" textAnchor="end">$3.5k</text>
          <text x="50" y="144" textAnchor="end">$3.0k</text>
          <text x="50" y="224" textAnchor="end">$2.5k</text>
          <text x="50" y="304" textAnchor="end">$2.0k</text>
          <text x="50" y="384" textAnchor="end">$1.5k</text>
        </g>

        <g className="xlab">
          <text x="60" y="408">$14</text>
          <text x="190" y="408">$17</text>
          <text x="320" y="408">$20</text>
          <text x="450" y="408">$23</text>
          <text x="580" y="408" textAnchor="end">$28</text>
        </g>

        <path
          id="cliff-fill"
          d="M 60 230 L 100 220 L 140 210 L 180 200 L 220 195 L 260 290 L 300 310 L 340 305 L 380 280 L 420 240 L 460 200 L 500 170 L 540 140 L 580 110 L 580 380 L 60 380 Z"
          fill="url(#cliff-grad)"
        />
        <path
          id="cliff-line"
          d="M 60 230 L 100 220 L 140 210 L 180 200 L 220 195 L 260 290 L 300 310 L 340 305 L 380 280 L 420 240 L 460 200 L 500 170 L 540 140 L 580 110"
          fill="none"
          stroke="#FB7185"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        <rect x="220" y="60" width="80" height="320" fill="rgba(251,113,133,0.08)" />
        <text x="260" y="50" textAnchor="middle" className="cliff-label">
          {cliffZoneLabel}
        </text>

        {/* T31 — cliff-edge annotation at $19 (x ≈ 246) */}
        <g
          data-annotation="cliff"
          onPointerEnter={() => setHovered("cliff")}
          onPointerLeave={() => setHovered((h) => (h === "cliff" ? null : h))}
          onFocus={() => setHovered("cliff")}
          onBlur={() => setHovered((h) => (h === "cliff" ? null : h))}
          tabIndex={0}
          style={{ cursor: "pointer" }}
        >
          <circle cx="246" cy="290" r="10" fill="rgba(251,113,133,0.35)" />
          <circle cx="246" cy="290" r="4" fill="#FB7185" />
        </g>

        {/* T31 — destination annotation at $22.50 (x ≈ 376) */}
        <g
          data-annotation="destination"
          onPointerEnter={() => setHovered("destination")}
          onPointerLeave={() => setHovered((h) => (h === "destination" ? null : h))}
          onFocus={() => setHovered("destination")}
          onBlur={() => setHovered((h) => (h === "destination" ? null : h))}
          tabIndex={0}
          style={{ cursor: "pointer" }}
        >
          <circle cx="376" cy="262" r="10" fill="rgba(34,211,238,0.35)" />
          <circle cx="376" cy="262" r="4" fill="#22D3EE" />
        </g>

        <g
          id="cliff-marker"
          transform={`translate(${markerX - 200}, ${markerY - 200})`}
        >
          <line
            x1="200"
            y1="60"
            x2="200"
            y2="380"
            stroke="rgba(245,235,210,0.4)"
            strokeWidth="1"
            strokeDasharray="3 3"
          />
          <circle cx="200" cy="200" r="6" fill="#F5F3EE" stroke="#FB7185" strokeWidth="2" />
          <circle
            cx="200"
            cy="200"
            r="14"
            fill="none"
            stroke="rgba(251,113,133,0.4)"
            strokeWidth="1"
          />
        </g>
      </svg>

      {tipText ? (
        <div
          role="tooltip"
          className="ch07-tooltip"
          style={{
            top: hovered === "cliff" ? "60%" : "55%",
            left: hovered === "cliff" ? "38%" : "60%",
          }}
        >
          {tipText}
        </div>
      ) : null}
    </div>
  );
}
