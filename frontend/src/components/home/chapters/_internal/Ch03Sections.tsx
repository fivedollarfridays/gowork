"use client";

/**
 * Chapter 03 internal section components — Portrait, Paragraphs, Facts.
 *
 * Pulled out of Chapter03MeetCarlos.tsx to keep the parent file under arch
 * limits (< 400 lines, < 15 functions).
 */

import type { CSSProperties } from "react";
import { CarlosPortraitSvg } from "./CarlosPortraitSvg";

interface PortraitProps {
  captionEyebrow: string;
  captionQuote: string;
  portraitAlt: string;
}

export function Ch03Portrait({
  captionEyebrow,
  captionQuote,
  portraitAlt,
}: PortraitProps) {
  return (
    <div
      className="ch03-portrait"
      data-gradient-border="on"
      style={portraitWrapStyle()}
    >
      <CarlosPortraitSvg alt={portraitAlt} />
      <div className="ch03-caption" style={captionStyle()}>
        <span className="cap-eb" style={captionEbStyle()}>
          {captionEyebrow}
        </span>
        <span className="cap-line" style={captionLineStyle()}>
          “{captionQuote}”
        </span>
      </div>
    </div>
  );
}

function portraitWrapStyle(): CSSProperties {
  return {
    position: "relative",
    aspectRatio: "4 / 5",
    borderRadius: "24px",
    overflow: "hidden",
    boxShadow: "0 40px 100px rgba(5,8,18,0.55)",
  };
}

function captionStyle(): CSSProperties {
  return {
    position: "absolute",
    bottom: "24px",
    left: "24px",
    right: "24px",
    padding: "18px 22px",
    background: "rgba(10,14,26,0.86)",
    backdropFilter: "blur(18px) saturate(140%)",
    WebkitBackdropFilter: "blur(18px) saturate(140%)",
    border: "1px solid color-mix(in oklch, var(--fg-primary), transparent 80%)",
    borderRadius: "14px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    color: "var(--fg-primary)",
  };
}

function captionEbStyle(): CSSProperties {
  return {
    fontFamily: "var(--font-mono-data)",
    fontSize: "10.5px",
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: "var(--accent-amber)",
  };
}

function captionLineStyle(): CSSProperties {
  return {
    fontSize: "15px",
    lineHeight: 1.55,
    color: "var(--fg-primary)",
    fontStyle: "oblique -6deg",
  };
}

interface ParagraphsProps {
  t: (k: string) => string;
}

export function Ch03Paragraphs({ t }: ParagraphsProps) {
  const p1 = t("home.ch3.p1");
  const p1Zip = t("home.ch3.p1Zip");
  const p2 = t("home.ch3.p2");
  const p2Bold = t("home.ch3.p2Bold");
  const [p1a, p1b] = p1.split("{{zip}}");
  const [p2a, p2b] = p2.split("{{bold}}");
  return (
    <>
      <p className="ch03-p" style={pStyle()}>
        {p1a}
        <b style={{ color: "var(--fg-primary)", fontWeight: 600 }}>{p1Zip}</b>
        {p1b ?? ""}
      </p>
      <p className="ch03-p" style={pStyle()}>
        {p2a}
        <b style={{ color: "var(--fg-primary)", fontWeight: 600 }}>{p2Bold}</b>
        {p2b ?? ""}
      </p>
    </>
  );
}

function pStyle(): CSSProperties {
  return {
    fontSize: "16.5px",
    lineHeight: 1.65,
    color: "var(--fg-secondary)",
    maxWidth: "38rem",
  };
}

interface FactsProps {
  t: (k: string) => string;
}

/** Parse the integer prefix of a fact value ("2:30" → 2, "47" → 47).
 *  Returns 0 for unparsable so the count-up tween skips that fact. */
function parseLeadingInt(raw: string): number {
  const match = raw.match(/^(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
}

export function Ch03Facts({ t }: FactsProps) {
  const facts = [
    { num: t("home.ch3.fact1Num"), cap: t("home.ch3.fact1Cap") },
    { num: t("home.ch3.fact2Num"), cap: t("home.ch3.fact2Cap") },
    { num: t("home.ch3.fact3Num"), cap: t("home.ch3.fact3Cap") },
    { num: t("home.ch3.fact4Num"), cap: t("home.ch3.fact4Cap") },
  ];
  return (
    <div className="ch03-facts" style={factsGridStyle()}>
      {facts.map((f, i) => (
        <div
          key={i}
          className="fact"
          data-countup={parseLeadingInt(f.num)}
          style={{ display: "flex", flexDirection: "column", gap: "4px" }}
        >
          <span
            className="fact-num"
            data-stat-num=""
            style={factNumStyle()}
          >
            {f.num}
          </span>
          <span className="fact-cap" style={factCapStyle()}>
            {f.cap}
          </span>
        </div>
      ))}
    </div>
  );
}

function factsGridStyle(): CSSProperties {
  return {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "18px",
    marginTop: "16px",
    paddingTop: "28px",
    borderTop: "1px solid color-mix(in oklch, var(--fg-primary), transparent 88%)",
  };
}

function factNumStyle(): CSSProperties {
  return {
    fontFamily: "var(--font-mono-data)",
    fontVariantNumeric: "tabular-nums",
    fontSize: "32px",
    fontWeight: 600,
    letterSpacing: "-0.02em",
    color: "var(--fg-primary)",
  };
}

function factCapStyle(): CSSProperties {
  return {
    fontSize: "11px",
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    color: "var(--fg-muted)",
  };
}
