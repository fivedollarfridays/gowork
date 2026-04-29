"use client";

/**
 * Chapter 01 hero h1 — three editorial lines, kinetic morph word.
 *
 * Pulled out of Chapter01TheWall.tsx to keep the parent under arch limits.
 * Caller owns the morph cycle; this component just renders the current
 * morphWord into `#morph-word`.
 */

import type { CSSProperties } from "react";

export interface Chapter01HeroProps {
  morphWord: string;
  ariaLabel: string;
  line2Wall: string;
  line2Job: string;
  line3Down: string;
}

export function Chapter01Hero({
  morphWord,
  ariaLabel,
  line2Wall,
  line2Job,
  line3Down,
}: Chapter01HeroProps) {
  return (
    <h1
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
      }}
    >
      <span className="line line-1" style={line1Style()}>
        <span id="morph-word" className="morph" style={morphStyle()}>
          {morphWord}
        </span>
      </span>

      <span className="line line-2" style={line2Style()}>
        There is a{" "}
        <em style={emStyle()}>{line2Wall}</em>
        {" "}between you and{" "}
        <span className="morph-target" style={morphTargetStyle()}>
          {line2Job}
        </span>
      </span>

      <span className="line line-3 italic-axis" style={line3Style()}>
        We tear it{" "}
        <span className="morph-action" style={morphActionStyle()}>
          {line3Down}
        </span>
        {" "}— brick by brick.
      </span>
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

function morphStyle(): CSSProperties {
  return {
    display: "inline-block",
    background:
      "linear-gradient(95deg, var(--accent-amber) 0%, var(--accent-rose) 60%, var(--accent-cyan) 100%)",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
    fontStyle: "oblique -10deg",
    willChange: "transform, opacity",
    padding: "0 5px 0 0",
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
  };
}

function emStyle(): CSSProperties {
  return {
    fontStyle: "oblique -8deg",
    color: "var(--accent-amber)",
    textDecoration: "line-through",
    textDecorationColor:
      "color-mix(in oklch, var(--accent-amber), transparent 50%)",
    textDecorationThickness: "4px",
  };
}

function morphTargetStyle(): CSSProperties {
  return {
    background:
      "linear-gradient(90deg, var(--accent-cyan), var(--accent-cyan-300))",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    color: "transparent",
    fontWeight: 800,
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
