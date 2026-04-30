"use client";

/**
 * Chapter 01 eyebrow chip: live-pulse dot + the HackFW 2026 framing.
 *
 * Visual upgrade: the chip now reads as a "broadcast badge" with
 * three layered effects:
 *   1. A pulsing amber `live` dot with concentric expanding rings
 *      (radar / heartbeat aesthetic) — drives the "live in production"
 *      claim home as motion, not just text.
 *   2. A subtle frosted-glass body (backdrop-filter blur + saturate)
 *      with a soft gradient border that picks up cyan + amber so the
 *      chip ties into the brand palette.
 *   3. A gentle ambient glow halo that breathes in sync with the dot.
 *
 * Wrapper has `.ch01-eyebrow-pill` so the keyframes + ::before /
 * ::after pseudos in home-velocity.css can target it. Reduced-motion
 * users get the static dot + no animations.
 */

interface Chapter01EyebrowProps {
  label: string;
}

export function Chapter01Eyebrow({ label }: Chapter01EyebrowProps) {
  return (
    <div
      className="ch01-eb ch01-eyebrow-pill"
      style={{
        position: "relative",
        zIndex: 2,
        margin: "0 auto",
        display: "inline-flex",
        alignItems: "center",
        gap: "10px",
        padding: "8px 18px",
        borderRadius: "999px",
        fontFamily: "var(--font-mono-data)",
        fontSize: "11px",
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: "var(--fg-secondary)",
        width: "fit-content",
        // Frosted-glass interior + saturated backdrop for depth.
        background:
          "linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(34, 211, 238, 0.06))",
        backdropFilter: "blur(10px) saturate(160%)",
        WebkitBackdropFilter: "blur(10px) saturate(160%)",
        border: "1px solid color-mix(in oklch, var(--fg-primary), transparent 80%)",
        boxShadow:
          "0 4px 14px rgba(10, 14, 26, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.08)",
      }}
    >
      {/* Live pulse — three nested elements:
          - Outer ring: scales 1 → 2.4, opacity 0.6 → 0 (radar wave)
          - Middle ring: scales 1 → 1.8 with 0.45s delay (second wave)
          - Inner dot: solid amber, brief opacity pulse */}
      <span
        className="ch01-eyebrow-pill__live"
        aria-hidden="true"
      >
        <span className="ch01-eyebrow-pill__ring ch01-eyebrow-pill__ring--outer" />
        <span className="ch01-eyebrow-pill__ring ch01-eyebrow-pill__ring--mid" />
        <span className="ch01-eyebrow-pill__dot" />
      </span>
      <span>{label}</span>
    </div>
  );
}
