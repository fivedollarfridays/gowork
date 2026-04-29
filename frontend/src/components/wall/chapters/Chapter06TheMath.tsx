"use client";

/**
 * W3 Driver A — Chapter 06 The Math (T3.1, T3.2, T3.3).
 *
 * The cliff chapter. Camera lands on Amazon FC DFW5 (Carlos's most
 * realistic warehouse employer reachable via Trinity Metro Bus 4).
 * A wage slider drives `--temperature-multiplier` (W3 Spotlight #1) so
 * the chapter scope responds visually as the user crosses known cliffs.
 * The embedded `BenefitsCliffChart` is IMPORTED from `components/plan`
 * — never re-implemented (W3 Spotlight #3 guards this).
 *
 * # A11y
 *   - h2 with id used by aria-labelledby on root section
 *   - aria-live narration on chapter activation
 *   - keyboard-reachable range slider with min/max/value labels
 *   - reduced-motion respected: no scroll-tied wage drift; user slider
 *     still interactive (the chart is the pedagogy, not the motion)
 *
 * # Sound
 *   - calculator-click on slider commit (`change` event = drag end /
 *     keyboard release). Rate-limited by browsers' native event cadence.
 *
 * # Honest uncertainty
 *   - BenefitsCliffChart accepts `analysis` only. We pass a static demo
 *     analysis derived from Carlos's profile so the cliff is VISIBLE
 *     even before the API hooks in. W4 polish can wire this to live
 *     `/api/cliff-analysis` results.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import type { ReactElement } from "react";
import dynamic from "next/dynamic";
import { t } from "@/lib/i18n";
import { useAriaAnnounce } from "@/components/wall/AriaLiveRegion";
import { play as playSound } from "@/lib/wall/sound";
import { CliffChartSkeleton } from "./CliffChartSkeleton";
import {
  MIN_WAGE_USD,
  MAX_WAGE_USD,
  setTemperatureMultiplier,
  wageToMultiplier,
} from "@/lib/wall/tempMultiplier";
import {
  CARLOS_DEMO_CLIFF_ANALYSIS,
  WAGE_SLIDER_DEFAULT,
  WAGE_SLIDER_STEP,
  formatWageUsd,
} from "@/lib/wall/chapters/ch6Math";

// W3 Driver D — Wave 3 bundle recovery: BenefitsCliffChart pulls in Recharts
// (~130KB minified). Loading it via next/dynamic with ssr:false keeps that
// dependency out of the eager chunk for `/`. The skeleton renders during
// hydration so there's no layout shift when the chart arrives. Until lazy:
// `/` First Load JS = 273KB. After lazy: target < 200KB. The bundleBudget
// regression-guard test pins this contract.
const BenefitsCliffChart = dynamic(
  () =>
    import("@/components/plan/BenefitsCliffChart").then((m) => ({
      default: m.BenefitsCliffChart,
    })),
  {
    ssr: false,
    loading: () => <CliffChartSkeleton />,
  },
);

export interface Chapter06TheMathProps {
  /** Local Ch6 progress 0..1. */
  progress: number;
  /** True when this chapter is the active scroll target. */
  active: boolean;
  /** Optional reduced-motion override; chapter consults the hook fallback. */
  reducedMotion?: boolean;
}

export function Chapter06TheMath({
  progress: _progress,
  active,
  reducedMotion = false,
}: Chapter06TheMathProps): ReactElement {
  void _progress; // currently unused in this chapter; reserved for parallax
  const announce = useAriaAnnounce();
  const enteredRef = useRef(false);
  const rootRef = useRef<HTMLElement | null>(null);
  const [wage, setWage] = useState<number>(WAGE_SLIDER_DEFAULT);

  // Apply the multiplier scoped to the chapter root. Synchronous on render
  // so SSR-paint reflects the slider's current value.
  useEffect(() => {
    if (!rootRef.current) return;
    setTemperatureMultiplier(wageToMultiplier(wage), rootRef.current);
  }, [wage]);

  useEffect(() => {
    if (!active) return;
    if (enteredRef.current) return;
    enteredRef.current = true;
    const aria = t("wall.chapter06.aria");
    if (aria) announce(aria);
  }, [active, announce]);

  const handleInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setWage(parseFloat(e.target.value));
  }, []);

  const handleCommit = useCallback(() => {
    playSound("calculator-click");
  }, []);

  return (
    <section
      ref={rootRef}
      data-testid="chapter06-the-math"
      data-chapter="06"
      data-chapter-id="the-math"
      data-reduced-motion={reducedMotion ? "true" : "false"}
      aria-labelledby="chapter06-title"
      className="chapter06-the-math relative flex min-h-screen flex-col items-center justify-center gap-6 px-6 py-16"
      style={{
        background:
          "linear-gradient(180deg, color-mix(in oklch, var(--bg-base) 70%, transparent) 0%, color-mix(in oklch, var(--bg-base) 95%, transparent) 100%)",
      }}
    >
      <h2
        id="chapter06-title"
        data-testid="ch6-hero"
        className="font-semibold tracking-tight text-center"
        style={{
          color: "var(--fg-primary)",
          maxWidth: "min(80vw, 60rem)",
          fontSize: "clamp(2rem, 4vw, 3.5rem)",
          letterSpacing: "-0.03em",
          lineHeight: 1.1,
          margin: 0,
        }}
      >
        {t("wall.chapter06.hero")}
      </h2>

      <p
        data-testid="ch6-subhero"
        className="text-center leading-relaxed"
        style={{
          color: "var(--fg-secondary, var(--fg-primary))",
          maxWidth: "min(72vw, 50rem)",
          fontSize: "clamp(1.0625rem, 1.5vw, 1.375rem)",
        }}
      >
        {t("wall.chapter06.subhero")}
      </p>

      <div
        data-testid="ch6-stat-pill"
        className="rounded-full px-4 py-2 text-sm font-medium"
        style={{
          background: "color-mix(in oklch, var(--accent-current) 25%, transparent)",
          color: "var(--fg-primary)",
        }}
      >
        <span data-testid="ch6-stat-value" className="font-bold">
          {t("wall.chapter06.statValue")}
        </span>{" "}
        <span className="opacity-80">{t("wall.chapter06.statLabel")}</span>
      </div>

      <Ch6WageSlider
        wage={wage}
        onInput={handleInput}
        onCommit={handleCommit}
      />

      <div
        data-testid="ch6-cliff-chart-host"
        className="w-full max-w-3xl"
        aria-label={t("wall.chapter06.cliffChartLabel")}
      >
        <BenefitsCliffChart analysis={CARLOS_DEMO_CLIFF_ANALYSIS} />
        <p
          className="mt-2 text-xs opacity-70"
          style={{ color: "var(--fg-secondary)" }}
        >
          {t("wall.chapter06.cliffChartCaption")}
        </p>
      </div>
    </section>
  );
}

interface SliderProps {
  wage: number;
  onInput: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onCommit: () => void;
}

/** Sub-component to keep the parent under arch limits. */
function Ch6WageSlider({ wage, onInput, onCommit }: SliderProps): ReactElement {
  return (
    <div className="flex w-full max-w-xl flex-col items-stretch gap-2">
      <label
        id="ch6-wage-slider-label"
        htmlFor="ch6-wage-slider"
        className="text-sm font-medium"
        style={{ color: "var(--fg-primary)" }}
      >
        {t("wall.chapter06.wageSliderLabel")}
      </label>
      <input
        id="ch6-wage-slider"
        data-testid="ch6-wage-slider"
        type="range"
        min={MIN_WAGE_USD}
        max={MAX_WAGE_USD}
        step={WAGE_SLIDER_STEP}
        value={wage}
        onInput={onInput}
        onChange={onCommit}
        aria-labelledby="ch6-wage-slider-label"
        className="w-full"
      />
      <div className="flex items-center justify-between text-xs" style={{ color: "var(--fg-secondary)" }}>
        <span data-testid="ch6-wage-slider-min">
          {t("wall.chapter06.wageSliderMinLabel")}
        </span>
        <span data-testid="ch6-wage-slider-value" className="font-semibold">
          {t("wall.chapter06.wageSliderValueLabel")}: {formatWageUsd(wage)}
        </span>
        <span data-testid="ch6-wage-slider-max">
          {t("wall.chapter06.wageSliderMaxLabel")}
        </span>
      </div>
      <p className="text-xs opacity-70" style={{ color: "var(--fg-secondary)" }}>
        {t("wall.chapter06.wageSliderHint")}
      </p>
    </div>
  );
}
