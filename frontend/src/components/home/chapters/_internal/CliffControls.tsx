"use client";

/**
 * Cliff slider + readout panel for Chapter 07.
 *
 * Owns the controlled `<input type="range">` and renders the readout rows
 * (Gross / SNAP / Childcare / Medicaid / Total). The math itself lives in
 * `cliffMath.ts`.
 *
 * polish-2 T32 — Adds a 4-state household-size segmented control beneath
 * the wage slider. Selecting a different household shifts the cliff
 * thresholds (1/2/3/4 → cliff edge $19/$21/$24/$27).
 *
 * polish-2 T30 — The chapter listens for forward crossings of the
 * Medicaid lapse threshold and momentarily sets `body[data-cliff-pulse]`
 * once per session. The crossing logic lives in the parent — this file
 * remains a pure UI surface that emits wage + household changes.
 */

import {
  wageGlowColor,
  wageGlowIntensity,
  type CliffOutputs,
  type MedicaidBucket,
  type HouseholdSize,
} from "./cliffMath";

interface CliffControlsProps {
  wage: number;
  onWageChange: (next: number) => void;
  household: HouseholdSize;
  onHouseholdChange: (next: HouseholdSize) => void;
  outputs: CliffOutputs;
  labels: ControlLabels;
}

export interface ControlLabels {
  controlsLabel: string;
  rowGross: string;
  rowSnap: string;
  rowCc: string;
  rowMed: string;
  rowTotal: string;
  medSafe: string;
  medAtRisk: string;
  medLapses: string;
  householdLabel: string;
  householdSize1: string;
  householdSize2: string;
  householdSize3: string;
  householdSize4: string;
}

const MED_LABEL_KEYS: Record<MedicaidBucket, keyof ControlLabels> = {
  safe: "medSafe",
  "at risk": "medAtRisk",
  lapses: "medLapses",
};

const HOUSEHOLD_OPTIONS: ReadonlyArray<HouseholdSize> = [1, 2, 3, 4];

function fmtDelta(v: number): string {
  if (v === 0) return "$0";
  const sign = v < 0 ? "−" : "+";
  return `${sign}$${Math.abs(v)}`;
}

function householdLabelFor(h: HouseholdSize, labels: ControlLabels): string {
  if (h === 1) return labels.householdSize1;
  if (h === 2) return labels.householdSize2;
  if (h === 3) return labels.householdSize3;
  return labels.householdSize4;
}

/** Slider upper bound per household. Cliff edges live at $19, $21,
 *  $24, $27 (matches `cliffEdgeForHousehold` in cliffMath.ts). Each
 *  household gets +$5 of slider room past its cliff so the user can
 *  drag fully into the lapse zone and see the rose halo trigger. */
function sliderMaxForHousehold(h: HouseholdSize): number {
  switch (h) {
    case 1:
      return 24;
    case 2:
      return 26;
    case 3:
      return 29;
    case 4:
    default:
      return 32;
  }
}

export function CliffControls({
  wage,
  onWageChange,
  household,
  onHouseholdChange,
  outputs,
  labels,
}: CliffControlsProps) {
  const totalPositive = outputs.total >= 0;
  const medLabel = labels[MED_LABEL_KEYS[outputs.medicaid]];

  return (
    <div
      className="ch07-controls"
      data-cliff-active={outputs.medicaid === "lapses" ? "true" : "false"}
      style={{
        marginTop: "16px",
        padding: "28px",
        // Match the right card's glass treatment: layered gradient
        // base + backdrop-filter for premium card chrome. Without
        // this, the controls panel read FLAT next to the rich
        // money-tower card on the right.
        background:
          "linear-gradient(160deg, rgba(15, 23, 41, 0.65) 0%, rgba(10, 14, 26, 0.55) 100%)",
        backdropFilter: "blur(14px) saturate(135%)",
        WebkitBackdropFilter: "blur(14px) saturate(135%)",
        border: `1px solid color-mix(in oklch, ${wageGlowColor(wage, household)}, transparent 65%)`,
        borderRadius: "20px",
        overflow: "hidden",
        // Continuous wage-state glow — same color as the right chart
        // card so the two panels read as a matched pair while the
        // user drags the slider. cyan (safe, far below cliff) →
        // amber (tipping at the edge) → rose (past the cliff).
        // Slightly softer alpha than the chart card so the user's eye
        // anchors to the data card on the right; controls are the
        // input, the chart is the readout.
        boxShadow: `0 24px 48px color-mix(in oklch, ${wageGlowColor(wage, household)}, transparent ${Math.round((1 - wageGlowIntensity(wage, household) * 0.85) * 100)}%), inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 0 0 1px color-mix(in oklch, ${wageGlowColor(wage, household)}, transparent 65%)`,
        transition:
          "box-shadow 540ms cubic-bezier(0.16, 1, 0.3, 1), border-color 540ms cubic-bezier(0.16, 1, 0.3, 1)",
        position: "relative",
      }}
    >
      <label
        className="ctrl-row"
        htmlFor="wage-slider"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: "14px",
        }}
      >
        <span
          className="ctrl-k"
          style={ctrlKeyStyle()}
        >
          {labels.controlsLabel}
        </span>
        <span
          className="ctrl-v"
          id="ctrl-v-wage"
          style={ctrlValStyle()}
        >
          ${wage.toFixed(2)}
        </span>
      </label>

      {/* Slider max scales with household: cliff edge is at $19/$21/
       *  $24/$27 for households 1/2/3/4. Each household needs ~$5
       *  of slider range above its cliff edge so the user can
       *  actually drag past the threshold and see the lapse fire.
       *  Was: hardcoded max=28, which gave family-of-4 only $1 of
       *  range past their $27 cliff (slider couldn't reach the
       *  rose halo state for that household). */}
      <input
        className="wage-slider"
        type="range"
        id="wage-slider"
        min="14"
        max={sliderMaxForHousehold(household)}
        step="0.25"
        value={wage}
        onChange={(e) => onWageChange(parseFloat(e.target.value))}
        aria-label={labels.controlsLabel}
        style={sliderStyle()}
      />

      <HouseholdSegmented
        household={household}
        onChange={onHouseholdChange}
        labels={labels}
      />

      <div
        className="ctrl-readout"
        style={{ display: "flex", flexDirection: "column", gap: "8px" }}
      >
        <ReadRow k={labels.rowGross} v={`$${Math.round(outputs.gross).toLocaleString("en-US")}`} />
        <ReadRow k={labels.rowSnap} v={fmtDelta(outputs.snapDelta)} tone="rose" />
        <ReadRow k={labels.rowCc} v={fmtDelta(outputs.ccDelta)} tone="rose" />
        <ReadRow k={labels.rowMed} v={medLabel} tone="rose" />
        <ReadRow
          k={labels.rowTotal}
          v={fmtDelta(outputs.total)}
          tone={totalPositive ? "green" : "rose"}
          total
        />
      </div>
    </div>
  );
}

function HouseholdSegmented({
  household,
  onChange,
  labels,
}: {
  household: HouseholdSize;
  onChange: (next: HouseholdSize) => void;
  labels: ControlLabels;
}) {
  return (
    <div
      className="ch07-household"
      role="radiogroup"
      aria-label={labels.householdLabel}
      style={{
        display: "flex",
        gap: "8px",
        marginBottom: "20px",
        padding: "4px",
        borderRadius: "999px",
        background: "color-mix(in oklch, var(--fg-primary), transparent 92%)",
      }}
    >
      <span
        style={{
          fontFamily: "var(--font-mono-data)",
          fontSize: "11px",
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--fg-muted)",
          alignSelf: "center",
          padding: "0 12px",
        }}
      >
        {labels.householdLabel}
      </span>
      {HOUSEHOLD_OPTIONS.map((h) => {
        const active = h === household;
        return (
          <button
            key={h}
            type="button"
            role="radio"
            aria-checked={active}
            data-testid={`ch07-household-${h}`}
            onClick={() => onChange(h)}
            style={{
              padding: "6px 14px",
              borderRadius: "999px",
              border: "1px solid color-mix(in oklch, var(--fg-primary), transparent 80%)",
              background: active ? "var(--accent-rose)" : "transparent",
              color: active ? "#0A0E1A" : "var(--fg-secondary)",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              fontFamily: "var(--font-mono-data)",
              transition: "all 220ms var(--ease-linear-sig)",
            }}
          >
            {householdLabelFor(h, labels)}
          </button>
        );
      })}
    </div>
  );
}

interface ReadRowProps {
  k: string;
  v: string;
  tone?: "rose" | "green";
  total?: boolean;
}

function ReadRow({ k, v, tone, total }: ReadRowProps) {
  const color = tone === "rose" ? "var(--accent-rose)" : tone === "green" ? "var(--status-positive)" : "var(--fg-primary)";
  return (
    <span
      className={total ? "r-row r-total" : "r-row"}
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
        padding: total ? "14px 0 6px" : "6px 0",
        fontFamily: "var(--font-mono-data)",
        marginTop: total ? "8px" : 0,
        borderTop: total
          ? "1px solid color-mix(in oklch, var(--fg-primary), transparent 86%)"
          : undefined,
      }}
    >
      <span
        className="r-k"
        style={{
          fontSize: "11.5px",
          color: total ? "var(--fg-primary)" : "var(--fg-muted)",
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          fontWeight: total ? 600 : 400,
        }}
      >
        {k}
      </span>
      <span
        className={tone ? `r-v ${tone}` : "r-v"}
        style={{
          fontSize: total ? "22px" : "16px",
          fontWeight: 600,
          color,
          fontVariantNumeric: "tabular-nums",
          letterSpacing: "-0.01em",
        }}
      >
        {v}
      </span>
    </span>
  );
}

function ctrlKeyStyle(): React.CSSProperties {
  return {
    fontFamily: "var(--font-mono-data)",
    fontSize: "11px",
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: "var(--fg-muted)",
  };
}

function ctrlValStyle(): React.CSSProperties {
  return {
    fontFamily: "var(--font-mono-data)",
    fontVariantNumeric: "tabular-nums",
    fontSize: "28px",
    fontWeight: 600,
    color: "var(--fg-primary)",
    letterSpacing: "-0.02em",
  };
}

function sliderStyle(): React.CSSProperties {
  return {
    width: "100%",
    appearance: "none",
    height: "4px",
    borderRadius: "2px",
    background:
      "linear-gradient(90deg, var(--status-positive) 0%, var(--status-positive) 35%, var(--accent-rose) 50%, var(--accent-rose) 65%, var(--status-positive) 80%, var(--status-positive) 100%)",
    outline: "none",
    cursor: "pointer",
    marginBottom: "20px",
  };
}
