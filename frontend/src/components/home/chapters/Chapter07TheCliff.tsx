"use client";

/**
 * Chapter 07 — The Cliff (Driver B + Driver C polish-2).
 *
 * Two-column: editorial left + cliff chart right. Slider updates the readout
 * and the chart marker live (no scroll required). Math lives in
 * `_internal/cliffMath.ts`; chart in `_internal/CliffChart.tsx`; controls in
 * `_internal/CliffControls.tsx`.
 *
 * polish-2 Driver C:
 *   - T30 — first forward crossing of the Medicaid lapse threshold
 *     (wage cross 17 with household=1; threshold scales) flashes a
 *     50ms screen-tint pulse and fires `useHaptic().error()` (10/30/10ms
 *     pattern). Crossing back doesn't re-trigger.
 *   - T31 — chart annotations + tooltip (delivered in CliffChart).
 *   - T32 — household-size segmented control under the slider.
 *   - T36 — first paragraph wrapped in `<DropCap chapter="7">`.
 *
 * # Reduced-motion contract
 *
 * The h2/controls entrance staggers are skipped under reduced motion. The
 * slider remains fully interactive (it's the user's input, not motion).
 */

import { useState, useRef, useEffect } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useGsapScrollTrigger } from "@/lib/home/gsap";
import { useHaptic } from "@/hooks/useHaptic";
import { computeCliff, type HouseholdSize } from "./_internal/cliffMath";
import { CliffChart } from "./_internal/CliffChart";
import { CliffControls } from "./_internal/CliffControls";
import { DropCap } from "../typography/DropCap";
import { TextReveal } from "@/components/home/_internal/TextReveal";

const DEFAULT_WAGE = 18.5;
const PULSE_THRESHOLD_WAGE = 17;
const PULSE_MS = 50;

/** Module-scoped one-shot guard — the pulse fires once per session
 *  (matches the W3 narrative: the wall has been seen). Lives outside
 *  the component so it survives unmount/remount within the same JS
 *  realm. */
let cliffPulsedThisSession = false;

/** Test-only — reset the one-shot pulse guard. Production never calls
 *  this; vitest beforeEach uses it to keep tests independent. */
export function __resetCliffPulseForTests(): void {
  cliffPulsedThisSession = false;
}

export interface Chapter07TheCliffProps {
  id?: string;
}

export function Chapter07TheCliff({ id = "chapter-07" }: Chapter07TheCliffProps) {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const haptic = useHaptic();
  const [wage, setWage] = useState<number>(DEFAULT_WAGE);
  const [household, setHousehold] = useState<HouseholdSize>(1);
  const outputs = computeCliff(wage, household);
  // Track whether the user has touched the slider yet. The pulse fires
  // on the first interaction that resolves to a wage at/above the
  // threshold; subsequent interactions never re-arm (per-session guard).
  const hasInteracted = useRef<boolean>(false);

  // T30 — one-shot pulse + haptic on first crossing in this session.
  useEffect(() => {
    if (!hasInteracted.current) return;
    if (cliffPulsedThisSession) return;
    if (wage < PULSE_THRESHOLD_WAGE) return;
    cliffPulsedThisSession = true;
    haptic.error();
    if (typeof document === "undefined") return;
    document.body.setAttribute("data-cliff-pulse", "true");
    const tid = window.setTimeout(() => {
      document.body.removeAttribute("data-cliff-pulse");
    }, PULSE_MS);
    return () => window.clearTimeout(tid);
  }, [wage, haptic]);

  const handleWageChange = (next: number) => {
    hasInteracted.current = true;
    setWage(next);
  };

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
      <Eyebrow t={t} />

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
            onWageChange={handleWageChange}
            household={household}
            onHouseholdChange={setHousehold}
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
              householdLabel: t("home.ch7.householdLabel"),
              householdSize1: t("home.ch7.householdSize1"),
              householdSize2: t("home.ch7.householdSize2"),
              householdSize3: t("home.ch7.householdSize3"),
              householdSize4: t("home.ch7.householdSize4"),
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
            tooltipCliff={t("home.ch7.cliff.tooltipEdge")}
            tooltipDestination={t("home.ch7.cliff.tooltipDestination")}
          />
        </div>
      </div>
    </section>
  );
}

function Eyebrow({ t }: { t: (k: string) => string }) {
  return (
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
    <div data-reveal-stagger style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <TextReveal direction="left" as="p" className="ch07-p" style={pStyle()}>
        <DropCap chapter="7">{p1A}</DropCap>
        <b style={{ color: "var(--fg-primary)", fontWeight: 600 }}>{p1Wage}</b>
        {p1B}
        <em style={{ color: "var(--accent-rose)", fontStyle: "normal" }}>{p1Loss}</em>
        {p1C ?? ""}
      </TextReveal>
      <TextReveal direction="left" as="p" className="ch07-p" style={pStyle()}>
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
      </TextReveal>
    </div>
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
