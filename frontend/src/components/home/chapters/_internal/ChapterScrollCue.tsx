"use client";

/**
 * Bottom-of-hero scroll cue: a small monospace label with a mouse-icon SVG
 * whose interior dot bobs.
 *
 * Positioned absolutely at bottom: 130px so it floats above the marquee but
 * inside the chapter section.
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
        bottom: "130px",
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
