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

import { useState, type ReactElement } from "react";

const SPOKEN_CITIES = ["Montgomery, AL", "Dallas, TX", "Houston, TX"] as const;

interface WordmarkProps {
  row1: string;
  row2: string;
  spokenCity: string;
  comingPrefix: string;
}

export function Ch08Wordmark({
  row1,
  row2,
  spokenCity,
  comingPrefix,
}: WordmarkProps): ReactElement {
  const [hovered, setHovered] = useState<boolean>(false);
  const [cityIdx, setCityIdx] = useState<number>(0);

  const onEnter = () => {
    setHovered(true);
    setCityIdx((i) => (i + 1) % SPOKEN_CITIES.length);
  };
  const onLeave = () => setHovered(false);

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
        className="wm-row wm-row-1"
        data-spoken-city={spokenCity}
        tabIndex={0}
        onPointerEnter={onEnter}
        onPointerLeave={onLeave}
        onFocus={onEnter}
        onBlur={onLeave}
        aria-label={`${spokenCity}. ${comingPrefix} ${SPOKEN_CITIES[cityIdx]}.`}
        style={row1Style()}
      >
        {row1}
      </span>
      <span className="wm-row wm-row-2" aria-hidden="true" style={row2Style()}>
        {row2}
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
