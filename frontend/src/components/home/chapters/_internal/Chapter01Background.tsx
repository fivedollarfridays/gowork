"use client";

/**
 * Chapter 01 background layers: 4 absolute panels (grid mask + amber glow +
 * cyan glow + noise) drifting via the `glow-drift` CSS keyframe.
 *
 * Pulled out of Chapter01TheWall.tsx to keep the parent file under arch
 * limits.
 *
 * # T13 — Grain texture intensifies on hover + fast scroll.
 *
 * The `.bg-noise` layer carries a `data-velocity-active` attribute that
 * the chapter sets to `"true"` when (a) the cursor enters the section, OR
 * (b) `useScrollVelocity().isFast` flips. The attribute drives a CSS rule
 * (in `home-chapters.css`) that bumps the noise opacity 0.06 → 0.12 with
 * a 600ms transition.
 */

export interface Chapter01BackgroundProps {
  /** When true, the bg-noise layer reads data-velocity-active="true" so
   *  the CSS rule can intensify the grain. */
  velocityActive?: boolean;
}

export function Chapter01Background({
  velocityActive = false,
}: Chapter01BackgroundProps = {}) {
  return (
    <div
      className="ch01-bg"
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        zIndex: 0,
        overflow: "hidden",
      }}
    >
      <div
        className="bg-grid"
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(245,235,210,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(245,235,210,0.04) 1px, transparent 1px)",
          backgroundSize: "80px 80px",
          maskImage:
            "radial-gradient(ellipse 80% 60% at 50% 40%, #000 30%, transparent 80%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 80% 60% at 50% 40%, #000 30%, transparent 80%)",
        }}
      />
      <div
        className="bg-glow bg-glow-amber"
        style={{
          position: "absolute",
          width: "60vw",
          height: "60vw",
          borderRadius: "999px",
          filter: "blur(120px)",
          opacity: 0.5,
          background:
            "radial-gradient(circle, rgba(245,158,11,0.45), transparent 60%)",
          top: "-20vw",
          left: "-20vw",
          animation: "glow-drift 18s ease-in-out infinite alternate",
        }}
      />
      <div
        className="bg-glow bg-glow-cyan"
        style={{
          position: "absolute",
          width: "60vw",
          height: "60vw",
          borderRadius: "999px",
          filter: "blur(120px)",
          opacity: 0.5,
          background:
            "radial-gradient(circle, rgba(34,211,238,0.35), transparent 60%)",
          bottom: "-25vw",
          right: "-15vw",
          animation: "glow-drift 18s ease-in-out infinite alternate -9s",
        }}
      />
      {/* polish-3 round-2 — cinematic mesh gradient. Three large radial
       * gradients drift on a 22s alternate keyframe. CSS-driven so the
       * GPU compositor handles the transform; no JS / no rerender. The
       * mesh sits BEHIND the grid + the static glow blobs, adding a
       * breathing color field that distinguishes our hero from a flat
       * noise background. */}
      <div className="ch01-mesh" aria-hidden="true" />
      <div
        className="bg-noise"
        data-velocity-active={velocityActive ? "true" : "false"}
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.06,
          mixBlendMode: "overlay",
          transition: "opacity 600ms ease",
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E\")",
        }}
      />
      {/* polish — horizontal scan beam. A thin cyan light line
       *  sweeps slowly down the hero every 18s, ducking beneath
       *  the typography via mix-blend-mode. Dribbble-grade ambient
       *  detail; the eye reads it as "the page is alive". */}
      <div className="ch01-scan" aria-hidden="true" />
      {/* polish — vignette mask. Soft dark feathering at the four
       *  corners so the central typography sits in a "spotlight"
       *  pool of color, not just on a flat panel. */}
      <div className="ch01-vignette" aria-hidden="true" />
      {/* polish — constellation dots. 12 small static cyan/amber
       *  pinpoints scattered across the field with individual
       *  twinkle phases, so the bg breathes even when the user
       *  isn't moving. */}
      <div className="ch01-stars" aria-hidden="true" />
    </div>
  );
}
