"use client";

/**
 * CliffMoneyTower — the wage-cliff visualization the line chart was
 * trying (and failing) to be.
 *
 * Replaces the line chart with a vertical "money stack" that
 * physically demonstrates the cliff: each component of monthly
 * take-home (gross wage, SNAP, childcare subsidy, Medicaid value)
 * is a glowing horizontal slab whose HEIGHT is proportional to its
 * dollar value. As the user pulls the wage slider, the gross slab
 * grows — but the benefits slabs SHRINK or DROP TO ZERO once their
 * income limits are crossed.
 *
 * When the user crosses the Medicaid lapse threshold (the cliff
 * edge), the Medicaid slab turns rose, glitches, and falls — a
 * visceral metaphor any worker can read instantly. No charts. No
 * axis labels. Just real dollars stacked tall, and the cliff-edge
 * moment shown as the whole stack getting SHORTER even though
 * wages went UP.
 *
 * Above the stack: a giant NET TAKE-HOME number (`outputs.total`)
 * that breathes its colour from cyan-safe → amber-warning → rose-
 * cliff as the user drags through the threshold zones.
 *
 * Reduced-motion contract: bars resize without springs, no glitch
 * pulse, no falling animation.
 */

import { useMemo } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import type { CliffOutputs, HouseholdSize } from "./cliffMath";

export interface CliffMoneyTowerProps {
  outputs: CliffOutputs;
  /** Household size 1-4. Drives baseline benefit values + the
   *  proportional delta scaling so the tower reads correctly for a
   *  single adult vs a family of four. */
  household: HouseholdSize;
  ariaLabel: string;
  cliffZoneLabel: string;
}

interface SlabSpec {
  label: string;
  value: number;
  /** Original "full benefit" value at the lowest wage. The ghost bar
   *  renders to this width; the actual fill renders to `value` width.
   *  The visible gap between ghost and fill IS the cliff loss. */
  baseline: number;
  color: string;
  glow: string;
  /** When the value goes negative (a "loss" relative to baseline),
   *  the slab inverts to rose to read as "money lost". */
  isLoss: boolean;
  /** Optional context hint shown beneath the label — e.g. "FAMILY OF 1". */
  hint?: string;
}

/**
 * Per-household benefit baselines. Numbers approximate Texas
 * benefit ceilings as of FY2024:
 *   - SNAP: max monthly allotment by household size (USDA)
 *   - CC:   CCAP childcare subsidy (zero for households with no
 *           kids; scales with #kids beyond that)
 *   - MED:  estimated monthly value of Medicaid coverage (single
 *           adult vs family-of-N marketplace silver-plan equivalent)
 *
 * The cliffMath module emits ABSOLUTE delta values (-120, -312,
 * -340, -360 for SNAP) calibrated to the household-1 baseline.
 * We scale the visualized delta by the same household ratio so
 * the bar shrinkage reads PROPORTIONAL: a family of 4 losing
 * $360 looks like a smaller dent in their $1,158 SNAP than a
 * single adult losing $360 from $360 — exactly as it should.
 */
const BASELINES: Record<
  HouseholdSize,
  { snap: number; cc: number; med: number }
> = {
  1: { snap: 360, cc: 0, med: 380 },
  2: { snap: 660, cc: 260, med: 720 },
  3: { snap: 950, cc: 420, med: 1020 },
  4: { snap: 1158, cc: 520, med: 1280 },
};

/** Scale the cliffMath SNAP delta from its household-1 calibration
 *  up to the household's baseline. Caps at the baseline so the
 *  scaled delta never erases more than 100% of the benefit. */
function scaleDelta(
  rawDelta: number,
  baseHh1: number,
  baseTarget: number,
): number {
  if (baseHh1 === 0) return 0;
  const ratio = baseTarget / baseHh1;
  const scaled = rawDelta * ratio;
  // Clamp so |scaled| never exceeds the target baseline.
  if (scaled < -baseTarget) return -baseTarget;
  return scaled;
}

export function CliffMoneyTower({
  outputs,
  household,
  ariaLabel,
  cliffZoneLabel,
}: CliffMoneyTowerProps) {
  const reduced = usePrefersReducedMotion();

  const slabs = useMemo<SlabSpec[]>(() => {
    const baseline = BASELINES[household];
    const baselineHh1 = BASELINES[1];
    // Scale the household-1 calibrated cliff deltas up to this
    // household's benefit ceiling. A delta of -120 SNAP for a
    // single adult ($360 baseline) becomes -396 for a family of 4
    // ($1158 baseline) — same proportional erosion in either case.
    const snapDeltaScaled = scaleDelta(
      outputs.snapDelta,
      baselineHh1.snap,
      baseline.snap,
    );
    const ccDeltaScaled = baseline.cc === 0
      ? 0
      : scaleDelta(outputs.ccDelta, baselineHh1.cc, baseline.cc);
    const snap = Math.max(0, baseline.snap + snapDeltaScaled);
    const cc = Math.max(0, baseline.cc + ccDeltaScaled);
    const med =
      outputs.medicaid === "safe"
        ? baseline.med
        : outputs.medicaid === "at risk"
          ? baseline.med * 0.5
          : 0;
    return [
      {
        label: "GROSS WAGE",
        hint: `MONTHLY · 173 HRS · HH ${household}`,
        value: outputs.gross,
        baseline: outputs.gross, // gross = own baseline (no cliff erosion)
        color: "var(--accent-cyan)",
        glow: "rgba(34, 211, 238, 0.55)",
        isLoss: false,
      },
      {
        label: "SNAP",
        hint: "FOOD ASSISTANCE",
        value: snap,
        baseline: baseline.snap,
        color:
          baseline.snap > 0 && snap < baseline.snap * 0.5
            ? "var(--accent-rose)"
            : "var(--accent-amber)",
        glow:
          baseline.snap > 0 && snap < baseline.snap * 0.5
            ? "rgba(251, 113, 133, 0.55)"
            : "rgba(245, 158, 11, 0.55)",
        isLoss: baseline.snap > 0 && snap < baseline.snap * 0.6,
      },
      {
        label: "CHILDCARE",
        hint: baseline.cc === 0 ? "NO DEPENDENTS" : "CCAP SUBSIDY",
        value: cc,
        baseline: baseline.cc,
        color:
          baseline.cc > 0 && cc < baseline.cc * 0.5
            ? "var(--accent-rose)"
            : "var(--accent-amber)",
        glow:
          baseline.cc > 0 && cc < baseline.cc * 0.5
            ? "rgba(251, 113, 133, 0.55)"
            : "rgba(245, 158, 11, 0.55)",
        isLoss: baseline.cc > 0 && cc < baseline.cc * 0.6,
      },
      {
        label: "MEDICAID",
        hint: "HEALTH COVERAGE",
        value: med,
        baseline: baseline.med,
        color:
          outputs.medicaid === "lapses"
            ? "var(--accent-rose)"
            : outputs.medicaid === "at risk"
              ? "var(--accent-amber)"
              : "var(--accent-cyan)",
        glow:
          outputs.medicaid === "lapses"
            ? "rgba(251, 113, 133, 0.7)"
            : outputs.medicaid === "at risk"
              ? "rgba(245, 158, 11, 0.55)"
              : "rgba(34, 211, 238, 0.55)",
        isLoss: outputs.medicaid !== "safe",
      },
    ];
  }, [outputs, household]);

  // Total benefits LOST relative to the full-benefit baseline. Drives
  // the "Δ −$X / month" sub-counter under the NET amount.
  const totalLost = useMemo(() => {
    return slabs.reduce((acc, s) => {
      if (s.label === "GROSS WAGE") return acc;
      const delta = s.value - s.baseline;
      return acc + (delta < 0 ? -delta : 0);
    }, 0);
  }, [slabs]);

  // Max slab value for proportional bar widths. Tower needs a stable
  // visual ceiling so the gross-wage bar (up to $5,196/mo at $30/hr)
  // doesn't dwarf the benefit bars. Scale modestly with household so
  // a family-of-4's larger benefit baselines still leave the gross
  // wage bar visually dominant — but never let any single bar
  // overflow its track.
  const maxValue = useMemo(() => {
    const baseline = BASELINES[household];
    const benefitsCeiling =
      baseline.snap + baseline.cc + baseline.med + 800; // +headroom
    return Math.max(3500, benefitsCeiling);
  }, [household]);
  const cliffActive = outputs.medicaid === "lapses";

  // Net take-home colour: cyan-safe → amber-warning → rose-cliff.
  const netColor = cliffActive
    ? "var(--accent-rose)"
    : outputs.medicaid === "at risk"
      ? "var(--accent-amber)"
      : "var(--accent-cyan)";

  return (
    <div
      className="ch07-tower"
      role="img"
      aria-label={ariaLabel}
      data-cliff-active={cliffActive ? "true" : "false"}
      data-reduced={reduced ? "true" : undefined}
      style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "32px",
        padding: "12px 0 4px",
      }}
    >
      {/* Giant NET TAKE-HOME number — the headline figure. */}
      <div className="ch07-tower__net" style={netHeaderStyle()}>
        <span style={netLabelStyle()}>NET TAKE-HOME / MONTH</span>
        <span
          className="ch07-tower__amount"
          style={netAmountStyle(netColor)}
        >
          ${outputs.total.toLocaleString()}
        </span>
        {/* TOTAL BENEFITS LOST — pulses under the net amount any time
         *  the cliff is taking benefits away. Reads as the "hidden
         *  cost" of the wage raise, in plain dollars. */}
        {totalLost > 0 ? (
          <span style={lostCounterStyle(cliffActive)}>
            <span style={{ opacity: 0.7 }}>Δ</span>
            <span style={{ fontWeight: 700 }}>
              −${Math.round(totalLost).toLocaleString()}
            </span>
            <span style={{ opacity: 0.7 }}>BENEFITS LOST / MO</span>
          </span>
        ) : null}
        {cliffActive ? (
          <span style={cliffBadgeStyle()}>
            <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--accent-rose)", display: "inline-block" }} />
            {cliffZoneLabel}
          </span>
        ) : null}
      </div>

      {/* Stacked slabs — each row has a label column + bar track.
       *  The track contains:
       *    - GHOST BASELINE bar (faded outline at full-benefit width)
       *    - ACTUAL FILL      (current width, glowing brand colour)
       *    - VALUE LABEL      ($amount on the right, with delta arrow)
       *  When the actual fill is shorter than the baseline, the
       *  visible gap between them IS the cliff loss, made physically
       *  legible without any "chart-like" axis labels. */}
      <div className="ch07-tower__stack" style={stackStyle()}>
        {slabs.map((slab) => {
          const widthPct = Math.max(0.02, Math.min(1, slab.value / maxValue));
          const baselinePct = Math.max(
            0.02,
            Math.min(1, slab.baseline / maxValue),
          );
          const delta = Math.round(slab.value - slab.baseline);
          const showDelta = slab.label !== "GROSS WAGE" && delta !== 0;
          return (
            <div
              key={slab.label}
              className="ch07-slab"
              data-loss={slab.isLoss ? "true" : "false"}
              style={slabRowStyle()}
            >
              <div style={slabLabelColumnStyle()}>
                <span style={slabLabelStyle()}>{slab.label}</span>
                {slab.hint ? (
                  <span style={slabHintStyle()}>{slab.hint}</span>
                ) : null}
              </div>
              <div
                className="ch07-slab__track"
                style={{
                  ...slabBarTrackStyle(),
                  // Cliff-state glow uses INSET shadows only — the
                  // bar's outer box stays the SAME in every state,
                  // so nothing visually shifts as the cliff activates.
                  // Was outer `0 0 28px ${glow}` which extended past
                  // the card edge and got clipped by overflow:hidden,
                  // making the medicaid bar look truncated.
                  boxShadow: slab.isLoss
                    ? `inset 0 0 28px ${slab.glow}, inset 0 0 0 1px color-mix(in oklch, ${slab.color}, transparent 50%)`
                    : `inset 0 0 0 1px color-mix(in oklch, var(--fg-primary), transparent 88%)`,
                }}
              >
                {/* GHOST BASELINE — faded outline at the full-benefit
                 *  width. Renders BEHIND the actual fill so the user
                 *  sees "this is what it was supposed to be" relative
                 *  to "this is what's left". */}
                {slab.label !== "GROSS WAGE" ? (
                  <div
                    style={ghostBaselineStyle(baselinePct)}
                    aria-hidden="true"
                  />
                ) : null}
                <div
                  style={{
                    ...slabBarFillStyle(slab.color, slab.glow),
                    width: `${widthPct * 100}%`,
                  }}
                />
                <span style={slabValueStyle(slab.color)}>
                  ${Math.round(slab.value).toLocaleString()}
                  {showDelta ? (
                    <span style={deltaStyle(delta)}>
                      {delta < 0 ? "▼" : "▲"} ${Math.abs(delta).toLocaleString()}
                    </span>
                  ) : null}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function netHeaderStyle(): React.CSSProperties {
  return {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "8px",
  };
}

function netLabelStyle(): React.CSSProperties {
  return {
    fontFamily: "var(--font-mono-data)",
    fontSize: "10.5px",
    letterSpacing: "0.2em",
    textTransform: "uppercase",
    color: "var(--fg-muted)",
  };
}

function netAmountStyle(color: string): React.CSSProperties {
  return {
    fontSize: "clamp(3.4rem, 2rem + 5vw, 6.5rem)",
    fontWeight: 900,
    letterSpacing: "-0.04em",
    lineHeight: 0.95,
    color,
    fontVariantNumeric: "tabular-nums",
    textShadow: `0 0 48px ${color}, 0 8px 24px rgba(10, 14, 26, 0.6)`,
    transition:
      "color 480ms cubic-bezier(0.16, 1, 0.3, 1), text-shadow 480ms cubic-bezier(0.16, 1, 0.3, 1)",
  };
}

function cliffBadgeStyle(): React.CSSProperties {
  return {
    display: "inline-flex",
    alignItems: "center",
    gap: "8px",
    padding: "6px 14px",
    background: "rgba(251, 113, 133, 0.08)",
    border: "1px solid color-mix(in oklch, var(--accent-rose), transparent 50%)",
    borderRadius: "999px",
    fontFamily: "var(--font-mono-data)",
    fontSize: "10.5px",
    letterSpacing: "0.16em",
    textTransform: "uppercase",
    color: "var(--accent-rose)",
    marginTop: "4px",
    animation: "ch07-cliff-pulse 1.4s ease-in-out infinite",
  };
}

/** Total-benefits-lost sub-counter style. Sits under the NET amount.
 *  Grayscale by default; pulses rose when the cliff is active. */
function lostCounterStyle(cliffActive: boolean): React.CSSProperties {
  return {
    display: "inline-flex",
    alignItems: "center",
    gap: "10px",
    padding: "5px 14px",
    background: cliffActive
      ? "rgba(251, 113, 133, 0.10)"
      : "rgba(245, 158, 11, 0.08)",
    border: cliffActive
      ? "1px solid color-mix(in oklch, var(--accent-rose), transparent 55%)"
      : "1px solid color-mix(in oklch, var(--accent-amber), transparent 55%)",
    borderRadius: "999px",
    fontFamily: "var(--font-mono-data)",
    fontSize: "11.5px",
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: cliffActive ? "var(--accent-rose)" : "var(--accent-amber)",
    fontVariantNumeric: "tabular-nums",
    marginTop: "2px",
  };
}

function stackStyle(): React.CSSProperties {
  return {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    width: "100%",
    paddingTop: "20px",
    borderTop: "1px solid color-mix(in oklch, var(--fg-primary), transparent 88%)",
  };
}

function slabRowStyle(): React.CSSProperties {
  return {
    display: "grid",
    gridTemplateColumns: "140px 1fr",
    alignItems: "center",
    gap: "16px",
  };
}

/** Label column wraps the primary label + an optional hint sub-line.
 *  Stack vertically so each row reads "SNAP / FOOD ASSISTANCE" with a
 *  clear hierarchy. */
function slabLabelColumnStyle(): React.CSSProperties {
  return {
    display: "flex",
    flexDirection: "column",
    gap: "3px",
  };
}

function slabLabelStyle(): React.CSSProperties {
  return {
    fontFamily: "var(--font-mono-data)",
    fontSize: "11px",
    fontWeight: 600,
    letterSpacing: "0.16em",
    textTransform: "uppercase",
    color: "var(--fg-primary)",
  };
}

/** Smaller hint line beneath the label — context for the dollar
 *  source ("FOOD ASSISTANCE" / "CCAP SUBSIDY" / etc.). */
function slabHintStyle(): React.CSSProperties {
  return {
    fontFamily: "var(--font-mono-data)",
    fontSize: "9px",
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    color: "var(--fg-muted)",
  };
}

/** Ghost baseline bar — sits behind the actual fill at the
 *  baseline width, dashed outline + low opacity so the gap between
 *  ghost and fill IS the cliff loss made visible. */
function ghostBaselineStyle(baselinePct: number): React.CSSProperties {
  return {
    position: "absolute",
    inset: 0,
    width: `${baselinePct * 100}%`,
    border:
      "1px dashed color-mix(in oklch, var(--fg-primary), transparent 65%)",
    borderRadius: "inherit",
    background:
      "repeating-linear-gradient(135deg, transparent 0 6px, color-mix(in oklch, var(--fg-primary), transparent 92%) 6px 7px)",
    pointerEvents: "none",
    zIndex: 0,
    opacity: 0.55,
  };
}

/** Delta indicator — shows -$X with arrow next to the dollar value. */
function deltaStyle(delta: number): React.CSSProperties {
  return {
    marginLeft: "10px",
    fontSize: "11px",
    fontWeight: 700,
    letterSpacing: "0.06em",
    color:
      delta < 0 ? "var(--accent-rose)" : "color-mix(in oklch, var(--status-positive, #22D3EE), transparent 0%)",
    fontVariantNumeric: "tabular-nums",
    opacity: 0.95,
  };
}

function slabBarTrackStyle(): React.CSSProperties {
  return {
    position: "relative",
    height: "44px",
    borderRadius: "8px",
    background:
      "linear-gradient(180deg, rgba(15, 23, 41, 0.5), rgba(10, 14, 26, 0.7))",
    overflow: "hidden",
    transition:
      "box-shadow 540ms cubic-bezier(0.16, 1, 0.3, 1)",
  };
}

function slabBarFillStyle(color: string, glow: string): React.CSSProperties {
  return {
    position: "absolute",
    inset: 0,
    background: `linear-gradient(90deg, color-mix(in oklch, ${color}, transparent 30%), ${color})`,
    borderRadius: "inherit",
    boxShadow: `inset 0 1px 0 rgba(255, 255, 255, 0.18), 0 0 24px ${glow}`,
    transition:
      "width 720ms cubic-bezier(0.16, 1, 0.3, 1), background 540ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 540ms cubic-bezier(0.16, 1, 0.3, 1)",
  };
}

function slabValueStyle(color: string): React.CSSProperties {
  return {
    position: "relative",
    zIndex: 1,
    display: "block",
    textAlign: "right",
    paddingRight: "14px",
    paddingTop: "13px",
    fontFamily: "var(--font-mono-data)",
    fontSize: "15px",
    fontWeight: 700,
    fontVariantNumeric: "tabular-nums",
    color,
    textShadow: "0 1px 0 rgba(10, 14, 26, 0.8)",
    letterSpacing: "-0.01em",
  };
}
