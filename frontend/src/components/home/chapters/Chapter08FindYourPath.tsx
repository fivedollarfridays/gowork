"use client";

/**
 * Chapter 08 — Find Your Path (Driver B, sprint/gowork-facelift).
 *
 * Manifesto + giant Truus-style wordmark closer. Per Shawn's narrative-reset
 * directive (commit b233102) the deprecated "5,189 / 13 / 2 / MIT" stat band
 * is gone — just the four-line manifesto, the CTA-XL, and the wordmark.
 *
 * # Reduced-motion contract
 *
 * The line-by-line stagger reveal and the opposing-scrub on the wordmark
 * rows are skipped under `prefers-reduced-motion: reduce`. The manifesto
 * still renders; the wordmark still renders, just statically.
 */

import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useGsapScrollTrigger } from "@/lib/home/gsap";

export interface Chapter08FindYourPathProps {
  id?: string;
}

export function Chapter08FindYourPath({
  id = "chapter-08",
}: Chapter08FindYourPathProps) {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();

  const sectionRef = useGsapScrollTrigger<HTMLElement>(({ el, gsap, reduced: r }) => {
    if (r) return;
    gsap.from(el.querySelectorAll(".ch08-h2 .line"), {
      y: 60,
      opacity: 0,
      duration: 1.0,
      stagger: 0.14,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch08-h2"),
        start: "top 75%",
        toggleActions: "play none none reverse",
      },
    });
    gsap.from(el.querySelectorAll(".ch08-cta"), {
      y: 30,
      opacity: 0,
      duration: 0.8,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch08-cta"),
        start: "top 80%",
        toggleActions: "play none none reverse",
      },
    });
    gsap.to(el.querySelector(".ch08-wordmark .wm-row-1"), {
      xPercent: -8,
      scrollTrigger: {
        trigger: el.querySelector(".ch08-wordmark"),
        start: "top bottom",
        end: "bottom top",
        scrub: true,
      },
    });
    gsap.to(el.querySelector(".ch08-wordmark .wm-row-2"), {
      xPercent: 8,
      scrollTrigger: {
        trigger: el.querySelector(".ch08-wordmark"),
        start: "top bottom",
        end: "bottom top",
        scrub: true,
      },
    });
    gsap.from(el.querySelectorAll(".ch08-wordmark .wm-row"), {
      opacity: 0,
      y: 80,
      stagger: 0.18,
      duration: 1.2,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch08-wordmark"),
        start: "top 80%",
        toggleActions: "play none none reverse",
      },
    });
  });

  return (
    <section
      ref={sectionRef}
      id={id}
      data-bg="warm"
      data-screen-label="08 Find your path"
      data-motion={reduced ? "off" : "on"}
      aria-labelledby="ch08-h2"
      className="chapter ch08"
      style={{
        padding: "160px 80px 0",
        background:
          "linear-gradient(180deg, rgba(245,158,11,0.06), rgba(245,158,11,0.02) 60%, transparent)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        gap: "80px",
      }}
    >
      <div
        className="ch08-content"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "40px",
          maxWidth: "70rem",
        }}
      >
        <span
          className="ch08-eb"
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
            08
          </span>
          <span className="lab">{t("home.ch8.eyebrow")}</span>
        </span>

        <Manifesto t={t} />

        <div
          className="ch08-cta"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            alignItems: "flex-start",
          }}
        >
          <a
            className="cta cta-primary cta-xl"
            href="/assess"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "16px",
              padding: "22px 34px",
              borderRadius: "999px",
              background: "var(--accent-cyan)",
              color: "#0A0E1A",
              fontWeight: 600,
              fontSize: "18px",
              letterSpacing: "-0.01em",
              boxShadow:
                "0 8px 24px color-mix(in oklch, var(--accent-cyan), transparent 60%)",
            }}
          >
            <span>{t("home.ch8.ctaPrimary")}</span>
            <span className="cta-arr">→</span>
          </a>
          <span
            className="ch08-meta"
            style={{
              fontFamily: "var(--font-mono-data)",
              fontSize: "11.5px",
              letterSpacing: "0.06em",
              color: "var(--fg-muted)",
              marginLeft: "4px",
            }}
          >
            {t("home.ch8.ctaMeta")}
          </span>
        </div>
      </div>

      <Wordmark
        row1={t("home.ch8.wordmarkRow1")}
        row2={t("home.ch8.wordmarkRow2")}
      />
    </section>
  );
}

function Manifesto({ t }: { t: (k: string) => string }) {
  const line4Raw = t("home.ch8.line4");
  const tuesday = t("home.ch8.line4Tuesday");
  const [l4a, l4b] = line4Raw.split("{{tuesday}}");
  return (
    <h2
      id="ch08-h2"
      className="ch08-h2"
      style={{
        fontSize: "clamp(2.4rem, 1.4rem + 3.4vw, 6rem)",
        fontWeight: 800,
        letterSpacing: "-0.035em",
        lineHeight: 1.05,
      }}
    >
      <span className="line" style={{ display: "block" }}>
        {t("home.ch8.line1")}
      </span>
      <span
        className="line italic-axis"
        style={{ display: "block", fontStyle: "oblique -10deg" }}
      >
        {t("home.ch8.line2")}
      </span>
      <span className="line" style={{ display: "block" }}>
        {t("home.ch8.line3")}
      </span>
      <span className="line" style={{ display: "block" }}>
        {l4a}
        <em
          style={{
            background:
              "linear-gradient(90deg, var(--accent-amber), var(--accent-rose))",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            color: "transparent",
            fontStyle: "normal",
          }}
        >
          {tuesday}
        </em>
        {l4b ?? ""}
      </span>
    </h2>
  );
}

function Wordmark({ row1, row2 }: { row1: string; row2: string }) {
  return (
    <div
      className="ch08-wordmark"
      aria-hidden="true"
      style={{
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
        style={{
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
        }}
      >
        {row1}
      </span>
      <span
        className="wm-row wm-row-2"
        style={{
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
        }}
      >
        {row2}
      </span>
    </div>
  );
}
