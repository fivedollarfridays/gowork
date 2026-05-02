"use client";

/**
 * Plan-page fanfare primitives — the Ch08 mic-drop machinery,
 * detached from its scroll-pin choreography and re-purposed as a
 * one-shot mount-time entrance for the WIN moment.
 *
 * Reuses the SAME CSS classes that drive the homepage's Ch08 closer
 * (`.ch08-pixel-grid`, `.ch08-square`, `.ch08-brand-icon`,
 *  `.ch08-aberration`, `.ch08-mic-drop__lockup`) — no duplicated
 * styling, no risk of drift.  All animation here is mount-driven, not
 * scroll-driven, so it integrates cleanly with the regular page flow.
 *
 * Three primitives:
 *   <Ch08PixelGrid />     — 510 amber squares, brand-gradient mixed,
 *                            dissolve in over ~1.6s, capped at 0.35
 *                            section opacity so they never obscure
 *                            content.
 *   <Ch08BrandIcon />      — cream G-arc + 3 stacked cyan path-lines
 *                            (halo-wide, halo-mid, core).  Path draws
 *                            in via stroke-dashoffset 192 → 0.
 *   <Ch08CyanUnderline />  — the wordmark lockup's cyan accent line
 *                            (gradient + 6-layer cyan halo box-shadow
 *                            stack).  Scales from 0 → 1 horizontally.
 *
 * Each primitive respects ``prefers-reduced-motion`` — the pixel grid
 * is hidden via CSS already; the path-line is set to its final state;
 * the underline scales to 1 immediately.
 */

import { useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";

const PIXEL_COLS = 30;
const PIXEL_ROWS = 17;

// Brand gradient stops (hex) for the per-square colour mixing — same
// amber→rose→cyan pattern as Ch08 so the grid reads as the brand
// homepage gradient when fully filled.  Lifted verbatim from
// Chapter08FindYourPath.tsx.
const STOP_AMBER: [number, number, number] = [0xF5, 0x9E, 0x0B];
const STOP_ROSE: [number, number, number] = [0xFB, 0x71, 0x85];
const STOP_CYAN: [number, number, number] = [0x22, 0xD3, 0xEE];

function lerp(a: number, b: number, t: number): number {
  return Math.round(a + (b - a) * t);
}
function mixGradientStop(t: number): string {
  if (t <= 0.5) {
    const k = t / 0.5;
    return `rgb(${lerp(STOP_AMBER[0], STOP_ROSE[0], k)},${lerp(STOP_AMBER[1], STOP_ROSE[1], k)},${lerp(STOP_AMBER[2], STOP_ROSE[2], k)})`;
  }
  const k = (t - 0.5) / 0.5;
  return `rgb(${lerp(STOP_ROSE[0], STOP_CYAN[0], k)},${lerp(STOP_ROSE[1], STOP_CYAN[1], k)},${lerp(STOP_ROSE[2], STOP_CYAN[2], k)})`;
}


/**
 * Mount-driven amber pixel grid dissolve.  510 squares, priority-sorted
 * (bottom-biased + sine + random), filling in over ~1.6s on a
 * requestAnimationFrame loop.  No scroll, no GSAP — just a self-
 * contained timer so the receipt section feels like the homepage's
 * closing image, the moment Carlos arrives.
 */
// Single hardcoded opacity target for the pixel grid dissolve.  Lives
// here as a constant rather than a prop because (a) the audit-tokens
// script doesn't see CSS custom properties used inside inline
// <style>{...}> blocks, and (b) a single value is what the design
// calls for — a luminous-but-not-overwhelming brand wash.  Squares
// fade from 0 to this number via the shared keyframes below.
const PIXEL_GRID_TARGET_OPACITY = 0.62;

export function Ch08PixelGrid({
  durationMs = 1600,
}: {
  durationMs?: number;
}) {
  const reduced = useReducedMotion();
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (reduced) return;
    const root = rootRef.current;
    if (!root) return;
    if (root.childElementCount > 0) return;  // built already (StrictMode safe)

    // Build the 510 squares — same gradient-mix logic as Ch08.  Each
    // square gets its own animation-delay computed from a priority
    // sort (bottom-rows first + sine + random); a shared @keyframes
    // fades each from opacity 0 → 0.62.  CSS owns the animation, so
    // React StrictMode double-mounting and re-renders can't race the
    // dissolve.  No RAF, no setTimeout, no orphans.
    const total = PIXEL_ROWS * PIXEL_COLS;
    const cells: { el: HTMLDivElement; priority: number }[] = [];

    for (let row = 0; row < PIXEL_ROWS; row += 1) {
      for (let col = 0; col < PIXEL_COLS; col += 1) {
        const sq = document.createElement("div");
        sq.className = "ch08-square";
        const tStop = (col / (PIXEL_COLS - 1) + row / (PIXEL_ROWS - 1)) / 2;
        sq.style.background = mixGradientStop(tStop);
        const distanceFromBottom = PIXEL_ROWS - 1 - row;
        const basePriority = distanceFromBottom * 50;
        const randomFactor = Math.random() * 300;
        const waveEffect = Math.sin(col * 0.3) * 30;
        const priority = basePriority + randomFactor + waveEffect;
        cells.push({ el: sq, priority });
      }
    }

    // Sort + assign animation-delay (compressed 75% so the last
    // squares finish before t=durationMs).
    cells.sort((a, b) => a.priority - b.priority);
    const frag = document.createDocumentFragment();
    cells.forEach(({ el }, i) => {
      const delay = (i / total) * durationMs * 0.75;
      el.style.animation = `ch08-pixel-fade-in 0.48s ease-out ${delay}ms forwards`;
      frag.appendChild(el);
    });
    root.appendChild(frag);
  }, [reduced, durationMs]);

  return (
    <>
      <style>{`
        @keyframes ch08-pixel-fade-in {
          from { opacity: 0; }
          to   { opacity: ${PIXEL_GRID_TARGET_OPACITY}; }
        }
      `}</style>
      <div
        ref={rootRef}
        className="ch08-pixel-grid"
        data-ch08-pixel-grid
        aria-hidden="true"
        style={{
          // mix-blend-mode: screen makes the brand-mixed squares LIGHTEN
          // the dark navy bg-base underneath — instead of layering as
          // dim colors over near-black, the squares become luminous.
          mixBlendMode: "screen",
        }}
      />
    </>
  );
}


/**
 * Cream G-arc + cyan path-line brand icon.  Lifted verbatim from
 * Ch08 with one difference: the cyan line draws on mount instead of
 * waiting for the GSAP timeline to scrub.  Sized via a `size` prop so
 * the same icon can be rendered tiny in an eyebrow or hero-large in
 * a section.
 */
export function Ch08BrandIcon({
  size = 40,
  drawDelayMs = 600,
  drawDurationMs = 900,
}: {
  size?: number;
  drawDelayMs?: number;
  drawDurationMs?: number;
}) {
  const reduced = useReducedMotion();
  const rootRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (reduced) return;
    const svg = rootRef.current;
    if (!svg) return;
    const lines = svg.querySelectorAll<SVGElement>(".ch08-brand-icon__line");
    if (lines.length === 0) return;

    // Set initial state — fully-hidden dashoffset.
    lines.forEach((ln) => {
      (ln as unknown as SVGLineElement).style.strokeDashoffset = "192";
      (ln as unknown as SVGLineElement).style.transition =
        `stroke-dashoffset ${drawDurationMs}ms ease-in-out`;
    });

    // Trigger the draw after `drawDelayMs` so the pixel grid has had a
    // moment to dissolve in first.
    const t = window.setTimeout(() => {
      lines.forEach((ln) => {
        (ln as unknown as SVGLineElement).style.strokeDashoffset = "0";
      });
    }, drawDelayMs);

    return () => window.clearTimeout(t);
  }, [reduced, drawDelayMs, drawDurationMs]);

  return (
    <svg
      ref={rootRef}
      className="ch08-brand-icon"
      viewBox="0 0 18 16"
      aria-hidden="true"
      fill="none"
      preserveAspectRatio="xMidYMid meet"
      overflow="visible"
      style={{ width: size, height: size }}
    >
      <path
        d="M 14 8 A 6 6 0 1 0 8 14"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="ch08-brand-icon__arc"
      />
      <line
        x1={8}
        y1={8}
        x2={16}
        y2={8}
        strokeLinecap="round"
        className="ch08-brand-icon__line ch08-brand-icon__line--halo-wide"
      />
      <line
        x1={8}
        y1={8}
        x2={16}
        y2={8}
        strokeLinecap="round"
        className="ch08-brand-icon__line ch08-brand-icon__line--halo-mid"
      />
      <line
        x1={8}
        y1={8}
        x2={16}
        y2={8}
        strokeLinecap="round"
        className="ch08-brand-icon__line ch08-brand-icon__line--core"
      />
    </svg>
  );
}


/**
 * The cyan path-line that lives under the GoWork lockup.  Reuses
 * `.ch08-mic-drop__lockup::after` styles by simply applying that class
 * to a wrapper.  We just toggle `--lockup-line-scale` from 0 → 1 over
 * `durationMs` once the children have rendered.
 */
export function Ch08LockupUnderline({
  delayMs = 900,
  durationMs = 1100,
  children,
}: {
  delayMs?: number;
  durationMs?: number;
  children: React.ReactNode;
}) {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (reduced) {
      el.style.setProperty("--lockup-line-scale", "1");
      return;
    }
    el.style.setProperty("--lockup-line-scale", "0");
    el.style.setProperty(
      "transition",
      `--lockup-line-scale ${durationMs}ms ease-in-out`,
    );
    const t = window.setTimeout(() => {
      // Drive the scale via a CSS transition on a custom property.  Some
      // browsers don't transition raw `--var-name` declarations; for
      // those, snap to 1 anyway so the line is visible.
      el.style.setProperty("--lockup-line-scale", "1");
    }, delayMs);
    return () => window.clearTimeout(t);
  }, [reduced, delayMs, durationMs]);

  return (
    <span ref={ref} className="ch08-mic-drop__lockup" style={{ display: "inline-block" }}>
      {children}
    </span>
  );
}
