"use client";

/**
 * Chapter 01 hero h1 — three editorial lines, kinetic morph word.
 *
 * # T11 — Height-stable morph word.
 *
 * The morph word swap used to reflow lines 2/3 because each cycle word
 * had a different intrinsic width. We now render a hidden width-anchor
 * (the longest word in the cycle, whichever locale that is) and
 * absolute-position the active word over it. Layout becomes constant —
 * even though the rendered character stream changes 7 times.
 *
 * # T12 — Variable-font weight axis driven by scrollY.
 *
 * The h1 line-1 carries a `fontVariationSettings: "wght" N` axis driven
 * by `useHeroFontWeight(scrollProgress)`. scrollY 0 → 0.05 of viewport
 * height interpolates 700 → 900. Reduced-motion locks at 700.
 */

import { useEffect, useState, type CSSProperties } from "react";
import { useHeroFontWeight } from "@/hooks/useHeroFontWeight";
import { useCursorParallax } from "@/hooks/useCursorParallax";
import { MaskReveal } from "@/components/home/_internal/MaskReveal";

export interface Chapter01HeroProps {
  morphWord: string;
  morphWords: readonly string[];
  ariaLabel: string;
  line2Wall: string;
  line2Job: string;
  line3Down: string;
}

/** Visual-width tiebreaker: when two morph words have the same character
 *  count, the one made of *wider* glyphs (no spaces, broad lowercase like
 *  m/w/g/o) tends to render wider on screen. We score each word by counting
 *  wide glyphs and subtracting whitespace, then pick the highest score. */
function pickWidestWord(words: readonly string[]): string {
  if (words.length === 0) return "";
  let best = words[0];
  let bestScore = scoreWidth(best);
  for (let i = 1; i < words.length; i += 1) {
    const score = scoreWidth(words[i]);
    if (score > bestScore) {
      best = words[i];
      bestScore = score;
    }
  }
  return best;
}

function scoreWidth(word: string): number {
  const wide = /[mwgoabdpquMWGOABDPQU0-9]/g;
  const wideHits = (word.match(wide)?.length ?? 0);
  const spaces = (word.match(/\s/g)?.length ?? 0);
  // Length dominates; wide-glyph bonus + whitespace penalty break ties.
  return word.length * 10 + wideHits - spaces * 2;
}

function useScrollProgress(): number {
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    if (typeof window === "undefined") return;
    let raf: number | null = null;
    const sample = () => {
      const vh = window.innerHeight || 1;
      const y = window.scrollY ?? 0;
      // Map 0..0.2 of viewport (the hero zone) onto 0..1 progress.
      // useHeroFontWeight has its own internal trigger threshold (0.05).
      const p = Math.max(0, Math.min(1, y / (vh * 0.2)));
      setProgress(p);
      raf = null;
    };
    const onScroll = () => {
      if (raf === null) raf = window.requestAnimationFrame(sample);
    };
    sample();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (raf !== null) window.cancelAnimationFrame(raf);
    };
  }, []);
  return progress;
}

export function Chapter01Hero({
  morphWord,
  morphWords,
  ariaLabel,
  line2Wall,
  line2Job,
  line3Down,
}: Chapter01HeroProps) {
  const longest = pickWidestWord(morphWords) || "background";
  const scrollProgress = useScrollProgress();
  const fontWeightAxis = useHeroFontWeight(scrollProgress);
  // polish-3 round-2 — cursor parallax. The hero composition drifts up
  // to ±10px X / ±6px Y based on cursor distance from the viewport
  // center. Lerp-eased so the lag feels cinematic, not literal.
  const parallaxRef = useCursorParallax<HTMLHeadingElement>({ maxX: 10, maxY: 6 });

  return (
    <h1
      ref={parallaxRef}
      className="ch01-h1"
      id="ch01-h1"
      aria-label={ariaLabel}
      style={{
        position: "relative",
        zIndex: 2,
        fontWeight: 900,
        letterSpacing: "-0.045em",
        textAlign: "center",
        maxWidth: "100%",
        padding: "0 4vw",
        fontFeatureSettings: '"ss01", "ss02"',
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "18px",
        willChange: "transform",
      }}
    >
      {/* Line 1 — kinetic morph word. Wrap in MaskReveal so the giant
       *  word rises from below the line on first paint, not just fades. */}
      <MaskReveal
        as="span"
        className="line line-1"
        innerStyle={{ ...line1Style(), fontVariationSettings: fontWeightAxis }}
      >
        <span className="morph-anchor-wrap" style={anchorWrapStyle()}>
          <span
            className="morph-anchor"
            data-morph-anchor=""
            aria-hidden="true"
            style={anchorStyle()}
          >
            {longest}
          </span>
          <span id="morph-word" className="morph" style={morphStyle()}>
            {morphWord}
          </span>
          <span
            className="sr-only"
            data-morph-live=""
            aria-live="polite"
          >
            {morphWord}
          </span>
        </span>
      </MaskReveal>

      {/* Line 2 — declarative statement. Mask reveal with 220ms delay
       *  so it lands AFTER the morph word has settled. The "wall"
       *  emphasis word gets an animated strike line drawn across it
       *  via a CSS pseudo-element (ch01-strike class) — the line
       *  scales from 0 → 1 starting at 1.2s, AFTER the line has
       *  fully revealed, so the user reads "wall" then watches it
       *  get crossed out. The brick-wall metaphor literalised. */}
      <MaskReveal as="span" className="line line-2" innerStyle={line2Style()} delayMs={220}>
        There is a{" "}
        <em className="ch01-strike" style={emStyle()}>
          {line2Wall}
        </em>
        {" "}between you and{" "}
        <span className="morph-target" style={morphTargetStyle()}>
          {line2Job}
        </span>
      </MaskReveal>

      {/* Line 3 — italic-axis closer. Reveal at 440ms so the cascade
       *  reads top→bottom 0 → 220 → 440 ms. */}
      <MaskReveal
        as="span"
        className="line line-3 italic-axis"
        innerStyle={line3Style()}
        delayMs={440}
      >
        We tear it{" "}
        <span className="morph-action" style={morphActionStyle()}>
          {line3Down}
        </span>
        {" "}— brick by brick.
      </MaskReveal>
    </h1>
  );
}

function line1Style(): CSSProperties {
  return {
    display: "block",
    fontSize: "clamp(5rem, 2rem + 14vw, 16rem)",
    lineHeight: 0.85,
    letterSpacing: "-0.06em",
    minHeight: "0.9em",
    width: "100%",
  };
}

function anchorWrapStyle(): CSSProperties {
  return {
    position: "relative",
    display: "inline-block",
  };
}

function anchorStyle(): CSSProperties {
  // Visible to the layout engine (it sets the width) but invisible to the
  // user. We keep it accessible for the layout but not announced.
  return {
    display: "inline-block",
    visibility: "hidden",
    pointerEvents: "none",
  };
}

function morphStyle(): CSSProperties {
  return {
    position: "absolute",
    inset: 0,
    display: "inline-block",
    background:
      "linear-gradient(95deg, var(--accent-amber) 0%, var(--accent-rose) 60%, var(--accent-cyan) 100%)",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
    fontStyle: "oblique -10deg",
    willChange: "transform, opacity",
    // polish-3 fix — was `text-align: left` + `padding: 0 5px 0 0`,
    // which left-anchored shorter words ("wall", "pickup") inside the
    // bounding box of the longest anchor word ("background"). They
    // looked drifted-left vs the actual hero centerline. Center-align
    // every cycled word so they share the same visual midline.
    padding: 0,
    textAlign: "center",
  };
}

function line2Style(): CSSProperties {
  return {
    display: "block",
    fontSize: "clamp(1.8rem, 1rem + 2.6vw, 3.4rem)",
    fontWeight: 600,
    lineHeight: 1.25,
    letterSpacing: "-0.02em",
    color: "var(--fg-secondary)",
    maxWidth: "30ch",
    // polish-2 round-3 fix — flex-column parent only centers BLOCK
    // alignment; text inside still hangs left because the line itself
    // has no text-align. Force center so the constrained 30ch width
    // doesn't shift visually toward the left edge.
    textAlign: "center",
  };
}

function emStyle(): CSSProperties {
  // No CSS line-through here — the strike line is drawn by the
  // .ch01-strike pseudo-element (CSS animated scaleX) so the user
  // watches it cross out the word, rather than seeing a static
  // line at first paint.
  return {
    fontStyle: "oblique -8deg",
    color: "var(--accent-amber)",
    position: "relative",
    display: "inline-block",
  };
}

function morphTargetStyle(): CSSProperties {
  // `white-space: nowrap` keeps the "a job." phrase together as a
  // single unbreakable unit. Without this the browser wraps the
  // INTERNAL space ("a" on line N, "job." on line N+1) which reads
  // as a typographic mistake. Now the phrase moves as a unit if
  // the line is too narrow — much cleaner editorial flow.
  return {
    background:
      "linear-gradient(90deg, var(--accent-cyan), var(--accent-cyan-300))",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
    fontWeight: 800,
    whiteSpace: "nowrap",
  };
}

function line3Style(): CSSProperties {
  return {
    display: "block",
    fontSize: "clamp(1.4rem, 0.8rem + 1.8vw, 2.4rem)",
    fontWeight: 500,
    lineHeight: 1.3,
    letterSpacing: "-0.015em",
    color: "var(--fg-primary)",
    marginTop: "4px",
    textAlign: "center",
  };
}

function morphActionStyle(): CSSProperties {
  return {
    background: "linear-gradient(90deg, var(--status-positive), var(--accent-cyan))",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
    fontWeight: 800,
    fontStyle: "normal",
  };
}
