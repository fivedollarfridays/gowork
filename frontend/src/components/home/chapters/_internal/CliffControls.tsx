"use client";

/**
 * Cliff slider + readout panel for Chapter 07.
 *
 * Owns the controlled `<input type="range">` and renders the readout rows
 * (Gross / SNAP / Childcare / Medicaid / Total). The math itself lives in
 * `cliffMath.ts`.
 */

import type { CliffOutputs, MedicaidBucket } from "./cliffMath";

interface CliffControlsProps {
  wage: number;
  onWageChange: (next: number) => void;
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
}

const MED_LABEL_KEYS: Record<MedicaidBucket, keyof ControlLabels> = {
  safe: "medSafe",
  "at risk": "medAtRisk",
  lapses: "medLapses",
};

function fmtDelta(v: number): string {
  if (v === 0) return "$0";
  const sign = v < 0 ? "−" : "+";
  return `${sign}$${Math.abs(v)}`;
}

export function CliffControls({ wage, onWageChange, outputs, labels }: CliffControlsProps) {
  const totalPositive = outputs.total >= 0;
  const medLabel = labels[MED_LABEL_KEYS[outputs.medicaid]];

  return (
    <div
      className="ch07-controls"
      style={{
        marginTop: "16px",
        padding: "28px",
        background: "rgba(10,14,26,0.5)",
        border: "1px solid color-mix(in oklch, var(--accent-rose), transparent 70%)",
        borderRadius: "16px",
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
          style={{
            fontFamily: "var(--font-mono-data)",
            fontSize: "11px",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "var(--fg-muted)",
          }}
        >
          {labels.controlsLabel}
        </span>
        <span
          className="ctrl-v"
          id="ctrl-v-wage"
          style={{
            fontFamily: "var(--font-mono-data)",
            fontVariantNumeric: "tabular-nums",
            fontSize: "28px",
            fontWeight: 600,
            color: "var(--fg-primary)",
            letterSpacing: "-0.02em",
          }}
        >
          ${wage.toFixed(2)}
        </span>
      </label>

      <input
        className="wage-slider"
        type="range"
        id="wage-slider"
        min="14"
        max="28"
        step="0.25"
        value={wage}
        onChange={(e) => onWageChange(parseFloat(e.target.value))}
        aria-label={labels.controlsLabel}
        style={{
          width: "100%",
          appearance: "none",
          height: "4px",
          borderRadius: "2px",
          background:
            "linear-gradient(90deg, var(--status-positive) 0%, var(--status-positive) 35%, var(--accent-rose) 50%, var(--accent-rose) 65%, var(--status-positive) 80%, var(--status-positive) 100%)",
          outline: "none",
          cursor: "pointer",
          marginBottom: "24px",
        }}
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
