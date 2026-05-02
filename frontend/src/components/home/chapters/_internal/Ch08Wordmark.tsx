"use client";

/**
 * Driver C — polish-2 T34 — giant 2-row wordmark with hover speak-the-city.
 *
 * Extracted from Chapter08FindYourPath.tsx so the parent stays under the
 * 400-line architecture limit. Behavior:
 *   - row 1 carries `data-spoken-city="Fort Worth, TX"` and is keyboard-
 *     reachable (tabIndex=0).
 *   - hover/focus reveals a tooltip "GoWork is in Fort Worth, TX. Coming
 *     soon: <city>" cycling through 3 placeholder cities.
 *   - cyan path-line under the wordmark draws on hover (delivered via
 *     `home-chapters.css` polish-2 namespace block).
 */

import { useEffect, useRef, useState, type ReactElement } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

const SPOKEN_CITIES = ["Fort Worth, TX", "Dallas, TX", "Houston, TX", "San Antonio, TX", "Austin, TX"] as const;

interface WordmarkProps {
  row1: string;
  row2: string;
  spokenCity: string;
  comingPrefix: string;
}

/** Split a string into [letter, isSpace] tuples so the renderer can mask
 *  individual letters but keep word boundaries readable. */
function splitLetters(s: string): Array<{ ch: string; ws: boolean }> {
  return Array.from(s).map((ch) => ({ ch, ws: /\s/.test(ch) }));
}

/**
 * polish-3 round-2 — letter-by-letter wordmark with scroll-tied reveal.
 *
 * Was: two static rows with `transform: translateX(±3vw)` and no
 *   entrance animation. Just sat there.
 * Now: each row's letters are split into individual masks. As the user
 *   scrolls past, an IntersectionObserver triggers the row's revealed
 *   state, and each letter rises with a staggered delay (35ms apart).
 *   Row 1 reveals first; row 2 follows 280ms behind so the cascade
 *   reads top→bottom. The italic-axis on row 2 amplifies the second-
 *   beat feel.
 */
export function Ch08Wordmark({
  row1,
  row2,
  spokenCity,
  comingPrefix,
}: WordmarkProps): ReactElement {
  const [hovered, setHovered] = useState<boolean>(false);
  const [cityIdx, setCityIdx] = useState<number>(0);
  const reduced = usePrefersReducedMotion();
  const row1Ref = useRef<HTMLSpanElement | null>(null);
  const row2Ref = useRef<HTMLSpanElement | null>(null);

  const onEnter = () => {
    setHovered(true);
    setCityIdx((i) => (i + 1) % SPOKEN_CITIES.length);
  };
  const onLeave = () => setHovered(false);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    if (reduced) {
      row1Ref.current?.setAttribute("data-revealed", "true");
      row2Ref.current?.setAttribute("data-revealed", "true");
      return undefined;
    }
    if (typeof IntersectionObserver === "undefined") return undefined;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            (e.target as HTMLElement).setAttribute("data-revealed", "true");
            io.unobserve(e.target);
          }
        }
      },
      { threshold: 0.18, rootMargin: "0px 0px -8% 0px" },
    );
    if (row1Ref.current) io.observe(row1Ref.current);
    if (row2Ref.current) io.observe(row2Ref.current);
    return () => io.disconnect();
  }, [reduced]);

  const row1Letters = splitLetters(row1);
  const row2Letters = splitLetters(row2);

  return (
    <div
      className="ch08-wordmark"
      style={{
        position: "relative",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "stretch",
        fontWeight: 900,
        letterSpacing: "-0.06em",
        lineHeight: 0.78,
        color: "var(--fg-primary)",
        textAlign: "center",
        userSelect: "none",
        marginTop: "60px",
      }}
    >
      <span
        ref={row1Ref}
        className="wm-row wm-row-1"
        data-spoken-city={spokenCity}
        data-revealed="false"
        tabIndex={0}
        onPointerEnter={onEnter}
        onPointerLeave={onLeave}
        onFocus={onEnter}
        onBlur={onLeave}
        aria-label={`${spokenCity}. ${comingPrefix} ${SPOKEN_CITIES[cityIdx]}.`}
        style={row1Style()}
      >
        {row1Letters.map((l, i) =>
          l.ws ? (
            <span key={`r1-ws-${i}`}>&nbsp;</span>
          ) : (
            <span key={`r1-${i}`} data-letter-mask="true">
              <span
                data-letter-inner="true"
                style={{ transitionDelay: `${i * 35}ms` }}
              >
                {l.ch}
              </span>
            </span>
          ),
        )}
      </span>
      <span
        ref={row2Ref}
        className="wm-row wm-row-2"
        data-revealed="false"
        aria-hidden="true"
        style={row2Style()}
      >
        {row2Letters.map((l, i) =>
          l.ws ? (
            <span key={`r2-ws-${i}`}>&nbsp;</span>
          ) : (
            <span key={`r2-${i}`} data-letter-mask="true">
              <span
                data-letter-inner="true"
                style={{ transitionDelay: `${280 + i * 35}ms` }}
              >
                {l.ch}
              </span>
            </span>
          ),
        )}
      </span>
      {hovered ? (
        <div
          className="ch08-wordmark__tooltip"
          role="tooltip"
          style={tooltipStyle()}
        >
          GoWork is in {spokenCity}. {comingPrefix} {SPOKEN_CITIES[cityIdx]}.
        </div>
      ) : null}
    </div>
  );
}

function row1Style(): React.CSSProperties {
  return {
    display: "block",
    fontSize: "clamp(8rem, 4rem + 22vw, 36rem)",
    fontFeatureSettings: '"ss01"',
    background:
      "linear-gradient(180deg, var(--fg-primary) 60%, color-mix(in oklch, var(--fg-primary), transparent 70%))",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
    willChange: "transform",
    transform: "translateX(-3vw)",
  };
}

function row2Style(): React.CSSProperties {
  return {
    display: "block",
    fontSize: "clamp(8rem, 4rem + 22vw, 36rem)",
    fontFeatureSettings: '"ss01"',
    background:
      "linear-gradient(180deg, var(--accent-amber) 50%, color-mix(in oklch, var(--accent-amber), transparent 40%))",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
    willChange: "transform",
    transform: "translateX(3vw)",
    fontStyle: "oblique -10deg",
  };
}

function tooltipStyle(): React.CSSProperties {
  return {
    position: "absolute",
    bottom: "-44px",
    left: "50%",
    transform: "translateX(-50%)",
    padding: "8px 14px",
    borderRadius: "999px",
    background: "rgba(10,14,26,0.92)",
    border: "1px solid color-mix(in oklch, var(--accent-cyan), transparent 60%)",
    color: "var(--fg-primary)",
    fontSize: "13px",
    fontFamily: "var(--font-mono-data)",
    whiteSpace: "nowrap",
  };
}
