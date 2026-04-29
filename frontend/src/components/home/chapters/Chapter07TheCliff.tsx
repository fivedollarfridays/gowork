"use client";

/**
 * Chapter 07 — The Cliff (Driver B, sprint/gowork-facelift).
 *
 * Two-column: editorial left + cliff chart right. Slider updates the readout
 * and the chart marker live (no scroll required). Math lives in
 * `_internal/cliffMath.ts`; chart in `_internal/CliffChart.tsx`; controls in
 * `_internal/CliffControls.tsx`.
 *
 * # Reduced-motion contract
 *
 * The h2/controls entrance staggers are skipped under reduced motion. The
 * slider remains fully interactive (it's the user's input, not motion).
 */

import { useState } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useGsapScrollTrigger } from "@/lib/home/gsap";
import { computeCliff } from "./_internal/cliffMath";
import { CliffChart } from "./_internal/CliffChart";
import { CliffControls } from "./_internal/CliffControls";

const DEFAULT_WAGE = 18.5;

export interface Chapter07TheCliffProps {
  id?: string;
}

export function Chapter07TheCliff({ id = "chapter-07" }: Chapter07TheCliffProps) {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const [wage, setWage] = useState<number>(DEFAULT_WAGE);
  const outputs = computeCliff(wage);

  const sectionRef = useGsapScrollTrigger<HTMLElement>(({ el, gsap, reduced: r }) => {
    if (r) return;
    gsap.from(el.querySelectorAll(".ch07-h2"), {
      y: 50,
      opacity: 0,
      duration: 1.0,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch07-h2"),
        start: "top 80%",
        toggleActions: "play none none reverse",
      },
    });
    gsap.from(el.querySelectorAll(".ch07-controls, .ch07-chart"), {
      y: 40,
      opacity: 0,
      duration: 0.9,
      stagger: 0.15,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch07-grid"),
        start: "top 75%",
        toggleActions: "play none none reverse",
      },
    });
  });

  return (
    <section
      ref={sectionRef}
      id={id}
      data-bg="rose"
      data-screen-label="07 The cliff"
      data-motion={reduced ? "off" : "on"}
      aria-labelledby="ch07-h2"
      className="chapter ch07"
      style={{
        minHeight: "100vh",
        padding: "160px 80px",
        background:
          "linear-gradient(180deg, rgba(251,113,133,0.04) 0%, rgba(251,113,133,0.10) 100%)",
      }}
    >
      <div
        className="ch07-eb"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "14px",
          fontFamily: "var(--font-mono-data)",
          fontSize: "11px",
          letterSpacing: "0.16em",
          textTransform: "uppercase",
          color: "var(--fg-muted)",
          marginBottom: "40px",
        }}
      >
        <span className="num" style={{ color: "var(--accent-rose)", fontWeight: 600 }}>
          07
        </span>
        <span className="lab">{t("home.ch7.eyebrow")}</span>
        <span
          className="rule"
          aria-hidden="true"
          style={{
            flex: 1,
            height: "1px",
            background: "color-mix(in oklch, var(--fg-primary), transparent 88%)",
          }}
        />
      </div>

      <div
        className="ch07-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1.2fr",
          gap: "80px",
          alignItems: "center",
        }}
      >
        <div
          className="ch07-text"
          style={{ display: "flex", flexDirection: "column", gap: "24px" }}
        >
          <H2Headline t={t} />
          <Paragraphs t={t} />
          <CliffControls
            wage={wage}
            onWageChange={setWage}
            outputs={outputs}
            labels={{
              controlsLabel: t("home.ch7.controlsLabel"),
              rowGross: t("home.ch7.rowGross"),
              rowSnap: t("home.ch7.rowSnap"),
              rowCc: t("home.ch7.rowCc"),
              rowMed: t("home.ch7.rowMed"),
              rowTotal: t("home.ch7.rowTotal"),
              medSafe: t("home.ch7.medSafe"),
              medAtRisk: t("home.ch7.medAtRisk"),
              medLapses: t("home.ch7.medLapses"),
            }}
          />
        </div>

        <div
          className="ch07-chart"
          id="ch07-chart"
          style={{
            position: "relative",
            borderRadius: "16px",
            background: "rgba(10,14,26,0.4)",
            border: "1px solid color-mix(in oklch, var(--fg-primary), transparent 88%)",
            padding: "24px",
          }}
        >
          <CliffChart
            markerX={outputs.markerX}
            markerY={outputs.markerY}
            ariaLabel={t("home.ch7.chartAria")}
            cliffZoneLabel={t("home.ch7.cliffZone")}
          />
        </div>
      </div>
    </section>
  );
}

function H2Headline({ t }: { t: (k: string) => string }) {
  const raw = t("home.ch7.h2");
  const raise = t("home.ch7.h2Raise");
  const cost = t("home.ch7.h2Cost");
  const [a, mid] = raw.split("{{raise}}");
  const [b, c] = (mid ?? "").split("{{cost}}");
  return (
    <h2
      id="ch07-h2"
      className="ch07-h2"
      style={{
        fontSize: "clamp(2.4rem, 1.4rem + 3vw, 5rem)",
        fontWeight: 800,
        letterSpacing: "-0.035em",
        lineHeight: 1,
      }}
    >
      {a}
      <em
        style={{
          fontStyle: "oblique -8deg",
          color: "var(--accent-rose)",
        }}
      >
        {raise}
      </em>
      {b}
      <span className="italic-axis" style={{ fontStyle: "oblique -10deg" }}>
        {cost}
      </span>
      {c ?? ""}
    </h2>
  );
}

function Paragraphs({ t }: { t: (k: string) => string }) {
  const p1Raw = t("home.ch7.p1");
  const p1Wage = t("home.ch7.p1Wage");
  const p1Loss = t("home.ch7.p1Loss");
  const p2Raw = t("home.ch7.p2");
  const p2Real = t("home.ch7.p2Real");

  const [p1A, p1Mid] = p1Raw.split("{{wage}}");
  const [p1B, p1C] = (p1Mid ?? "").split("{{loss}}");
  const [p2A, p2B] = p2Raw.split("{{real}}");

  return (
    <>
      <p className="ch07-p" style={pStyle()}>
        {p1A}
        <b style={{ color: "var(--fg-primary)", fontWeight: 600 }}>{p1Wage}</b>
        {p1B}
        <em style={{ color: "var(--accent-rose)", fontStyle: "normal" }}>{p1Loss}</em>
        {p1C ?? ""}
      </p>
      <p className="ch07-p" style={pStyle()}>
        {p2A}
        <a
          className="editorial-link"
          href="/assess"
          style={{
            color: "var(--accent-cyan)",
            backgroundImage:
              "linear-gradient(90deg, var(--accent-cyan), var(--accent-amber))",
            backgroundPosition: "0 100%",
            backgroundRepeat: "no-repeat",
            backgroundSize: "100% 1px",
            paddingBottom: "1px",
          }}
        >
          {p2Real}
        </a>
        {p2B ?? ""}
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
