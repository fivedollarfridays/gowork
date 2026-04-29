"use client";

/**
 * Chapter 03 — Meet Carlos (Driver B, sprint/gowork-facelift).
 *
 * Two-column split: stylized SVG portrait left, editorial right.
 * Portrait parallaxes y -60px on scroll. h2 reveals word-by-word.
 *
 * # Reduced-motion contract
 *
 * Under reduced motion the parallax and word stagger are disabled — the
 * h2 renders in its final state and the portrait stays static.
 *
 * # polish-2 Driver B additions
 *
 * - T16 — portrait splits into 3 parallax z-layers (in CarlosPortraitSvg).
 * - T17 — `.ch03-portrait[data-gradient-border="on"]` border-image rule.
 * - T18 — facts hover-lift + count-up tween (in choreography).
 */

import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useGsapScrollTrigger } from "@/lib/home/gsap";
import {
  Ch03Portrait,
  Ch03Paragraphs,
  Ch03Facts,
} from "./_internal/Ch03Sections";
import { runCh03Choreography } from "./Chapter03MeetCarlos.choreography";

const FALLBACK_WORDS: readonly string[] = [
  "A",
  "father.",
  "A",
  "welder.",
  "Not",
  "a",
  "case",
  "number.",
];
const ITALIC_FROM = 4;

function readWords(t: (k: string) => string): readonly string[] {
  const raw = t("home.ch3.h2Words");
  if (raw && raw !== "home.ch3.h2Words" && raw.startsWith("[")) {
    try {
      const parsed = JSON.parse(raw) as unknown;
      if (Array.isArray(parsed) && parsed.every((v) => typeof v === "string")) {
        return parsed as string[];
      }
    } catch {
      /* fall through */
    }
  }
  return FALLBACK_WORDS;
}

export interface Chapter03MeetCarlosProps {
  id?: string;
}

export function Chapter03MeetCarlos({ id = "chapter-03" }: Chapter03MeetCarlosProps) {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const words = readWords(t);

  const sectionRef = useGsapScrollTrigger<HTMLElement>(
    ({ el, gsap, reduced: r }) => {
      if (r) return;
      runCh03Choreography(el, gsap as Parameters<typeof runCh03Choreography>[1]);
    },
  );

  return (
    <section
      ref={sectionRef}
      id={id}
      data-bg="warm"
      data-screen-label="03 Meet Carlos"
      data-motion={reduced ? "off" : "on"}
      aria-labelledby="ch03-h2"
      className="chapter ch03"
      style={{
        minHeight: "100vh",
        padding: "160px 80px",
        background:
          "linear-gradient(180deg, rgba(245,158,11,0.04) 0%, rgba(245,158,11,0.10) 40%, rgba(251,113,133,0.06) 100%)",
        overflow: "hidden",
      }}
    >
      <div
        className="ch03-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1.1fr",
          gap: "80px",
          maxWidth: "110rem",
          margin: "0 auto",
          alignItems: "center",
        }}
      >
        <Ch03Portrait
          captionEyebrow={t("home.ch3.captionEyebrow")}
          captionQuote={t("home.ch3.captionQuote")}
          portraitAlt={t("home.ch3.portraitAlt")}
        />

        <div
          className="ch03-text"
          style={{ display: "flex", flexDirection: "column", gap: "28px" }}
        >
          <span
            className="ch03-eb"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "12px",
              fontFamily: "var(--font-mono-data)",
              fontSize: "11px",
              letterSpacing: "0.16em",
              textTransform: "uppercase",
              color: "var(--fg-muted)",
            }}
          >
            <span className="num" style={{ color: "var(--accent-amber)", fontWeight: 600 }}>
              03
            </span>
            <span className="lab" style={{ color: "var(--fg-secondary)" }}>
              {t("home.ch3.eyebrow")}
            </span>
          </span>

          <h2
            id="ch03-h2"
            className="ch03-h2"
            style={{
              fontSize: "clamp(2.5rem, 1.5rem + 3vw, 5rem)",
              fontWeight: 800,
              letterSpacing: "-0.035em",
              lineHeight: 1,
            }}
          >
            {words.map((w, i) => (
              <span
                key={i}
                className={i >= ITALIC_FROM ? "word italic-axis" : "word"}
                style={{
                  display: "inline-block",
                  margin: "0 0.04em 0.04em 0",
                  fontStyle: i >= ITALIC_FROM ? "oblique -10deg" : "normal",
                }}
              >
                {w}
              </span>
            ))}
          </h2>

          <Ch03Paragraphs t={t} />

          <Ch03Facts t={t} />
        </div>
      </div>
    </section>
  );
}
