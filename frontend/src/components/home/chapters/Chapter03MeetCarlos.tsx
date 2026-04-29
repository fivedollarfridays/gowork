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
 */

import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useGsapScrollTrigger } from "@/lib/home/gsap";
import { CarlosPortraitSvg } from "./_internal/CarlosPortraitSvg";

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

  const sectionRef = useGsapScrollTrigger<HTMLElement>(({ el, gsap, reduced: r }) => {
    if (r) return;
    gsap.from(el.querySelectorAll(".ch03-portrait"), {
      x: -80,
      opacity: 0,
      duration: 1.2,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el,
        start: "top 60%",
        toggleActions: "play none none reverse",
      },
    });
    gsap.from(el.querySelectorAll(".ch03-h2 .word"), {
      y: 40,
      opacity: 0,
      duration: 0.8,
      stagger: 0.06,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch03-h2"),
        start: "top 70%",
        toggleActions: "play none none reverse",
      },
    });
    gsap.from(el.querySelectorAll(".ch03-p"), {
      y: 24,
      opacity: 0,
      duration: 0.8,
      stagger: 0.15,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch03-p"),
        start: "top 80%",
        toggleActions: "play none none reverse",
      },
    });
    gsap.from(el.querySelectorAll(".ch03-facts .fact"), {
      y: 24,
      opacity: 0,
      duration: 0.6,
      stagger: 0.1,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch03-facts"),
        start: "top 85%",
        toggleActions: "play none none reverse",
      },
    });
    gsap.to(el.querySelector(".ch03-portrait"), {
      y: -60,
      scrollTrigger: {
        trigger: el,
        start: "top bottom",
        end: "bottom top",
        scrub: true,
      },
    });
  });

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
        <Portrait
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
                className={
                  i >= ITALIC_FROM ? "word italic-axis" : "word"
                }
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

          <Paragraphs t={t} />

          <Facts t={t} />
        </div>
      </div>
    </section>
  );
}

function Portrait({
  captionEyebrow,
  captionQuote,
  portraitAlt,
}: {
  captionEyebrow: string;
  captionQuote: string;
  portraitAlt: string;
}) {
  return (
    <div
      className="ch03-portrait"
      style={{
        position: "relative",
        aspectRatio: "4 / 5",
        borderRadius: "24px",
        overflow: "hidden",
        boxShadow: "0 40px 100px rgba(5,8,18,0.55)",
        border: "1px solid color-mix(in oklch, var(--fg-primary), transparent 86%)",
      }}
    >
      <CarlosPortraitSvg alt={portraitAlt} />
      <div
        className="ch03-caption"
        style={{
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
        }}
      >
        <span
          className="cap-eb"
          style={{
            fontFamily: "var(--font-mono-data)",
            fontSize: "10.5px",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "var(--accent-amber)",
          }}
        >
          {captionEyebrow}
        </span>
        <span
          className="cap-line"
          style={{
            fontSize: "15px",
            lineHeight: 1.55,
            color: "var(--fg-primary)",
            fontStyle: "oblique -6deg",
          }}
        >
          “{captionQuote}”
        </span>
      </div>
    </div>
  );
}

function Paragraphs({ t }: { t: (k: string) => string }) {
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

function pStyle(): React.CSSProperties {
  return {
    fontSize: "16.5px",
    lineHeight: 1.65,
    color: "var(--fg-secondary)",
    maxWidth: "38rem",
  };
}

function Facts({ t }: { t: (k: string) => string }) {
  const facts = [
    { num: t("home.ch3.fact1Num"), cap: t("home.ch3.fact1Cap") },
    { num: t("home.ch3.fact2Num"), cap: t("home.ch3.fact2Cap") },
    { num: t("home.ch3.fact3Num"), cap: t("home.ch3.fact3Cap") },
    { num: t("home.ch3.fact4Num"), cap: t("home.ch3.fact4Cap") },
  ];
  return (
    <div
      className="ch03-facts"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: "18px",
        marginTop: "16px",
        paddingTop: "28px",
        borderTop: "1px solid color-mix(in oklch, var(--fg-primary), transparent 88%)",
      }}
    >
      {facts.map((f, i) => (
        <div
          key={i}
          className="fact"
          style={{ display: "flex", flexDirection: "column", gap: "4px" }}
        >
          <span
            className="fact-num"
            style={{
              fontFamily: "var(--font-mono-data)",
              fontVariantNumeric: "tabular-nums",
              fontSize: "32px",
              fontWeight: 600,
              letterSpacing: "-0.02em",
              color: "var(--fg-primary)",
            }}
          >
            {f.num}
          </span>
          <span
            className="fact-cap"
            style={{
              fontSize: "11px",
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--fg-muted)",
            }}
          >
            {f.cap}
          </span>
        </div>
      ))}
    </div>
  );
}
