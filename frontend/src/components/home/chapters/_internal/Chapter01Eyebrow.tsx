"use client";

/**
 * Chapter 01 eyebrow chip: live-pulse dot + the HackFW 2026 framing.
 *
 * Pulled into its own file to keep Chapter01TheWall.tsx under arch limits.
 */

interface Chapter01EyebrowProps {
  label: string;
}

export function Chapter01Eyebrow({ label }: Chapter01EyebrowProps) {
  return (
    <div
      className="ch01-eb"
      style={{
        position: "relative",
        zIndex: 2,
        margin: "0 auto",
        display: "inline-flex",
        alignItems: "center",
        gap: "10px",
        padding: "8px 16px",
        background: "color-mix(in oklch, var(--fg-primary), transparent 92%)",
        border: "1px solid color-mix(in oklch, var(--fg-primary), transparent 82%)",
        borderRadius: "999px",
        fontFamily: "var(--font-mono-data)",
        fontSize: "11px",
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        color: "var(--fg-secondary)",
        width: "fit-content",
      }}
    >
      <span
        className="dot dot-live"
        aria-hidden="true"
        style={{
          display: "inline-block",
          width: "6px",
          height: "6px",
          borderRadius: "999px",
          background: "var(--accent-amber)",
          boxShadow: "0 0 10px var(--accent-amber)",
        }}
      />
      <span>{label}</span>
    </div>
  );
}
