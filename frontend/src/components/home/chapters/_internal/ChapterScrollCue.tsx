"use client";

/**
 * Bottom-of-hero scroll cue: a small monospace label with a mouse-icon SVG
 * whose interior dot bobs.
 *
 * Position progression:
 *   bottom: 130px → collided with CTA row
 *   bottom: 24px  → INSIDE marquee, overlapped "OPEN COURT DATE"
 *   bottom: 110px → too high, clipped CTA row from the bottom
 *   bottom: 86px  → CURRENT. Sits in the gap between CTA row and
 *                   marquee strip. Marquee total height ≈ 70px
 *                   (24px padding × 2 + ~22px content) + 32px
 *                   margin-top above it. 86px clears the marquee
 *                   top edge with ~16px breathing room and stays
 *                   below the CTA row.
 */

export interface ChapterScrollCueProps {
  label: string;
}

export function ChapterScrollCue({ label }: ChapterScrollCueProps) {
  return (
    <div
      className="ch01-scroll-cue"
      aria-hidden="true"
      style={{
        position: "absolute",
        bottom: "86px",
        left: "50%",
        transform: "translate(-50%, 0)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "8px",
        fontFamily: "var(--font-mono-data)",
        fontSize: "10px",
        letterSpacing: "0.2em",
        textTransform: "uppercase",
        color: "var(--fg-muted)",
        zIndex: 3,
      }}
    >
      <span>{label}</span>
      <svg viewBox="0 0 16 24" width="14" height="22" aria-hidden="true">
        <rect
          x="1"
          y="1"
          width="14"
          height="22"
          rx="7"
          stroke="currentColor"
          strokeWidth="1.2"
          fill="none"
        />
        <circle
          className="cue-dot"
          cx="8"
          cy="7"
          r="2"
          fill="currentColor"
          style={{ animation: "cue-bob 1.8s ease-in-out infinite" }}
        />
      </svg>
    </div>
  );
}
