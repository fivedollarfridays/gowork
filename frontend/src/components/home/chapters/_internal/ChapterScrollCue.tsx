"use client";

/**
 * Bottom-of-hero scroll cue: a small monospace label with a mouse-icon SVG
 * whose interior dot bobs.
 *
 * polish-3 fix — was previously `bottom: 130px` which planted the cue
 * directly on top of the "Get your plan" CTA row. Moved to `bottom: 24px`
 * (under the marquee, at the section's true bottom edge) so it never
 * collides with the CTAs.
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
        bottom: "24px",
        left: "50%",
        transform: "translateX(-50%)",
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
