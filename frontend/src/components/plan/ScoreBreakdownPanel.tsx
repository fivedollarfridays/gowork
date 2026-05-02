"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import type { ScoreBreakdown } from "@/lib/types";

interface ScoreBreakdownPanelProps {
  breakdown: ScoreBreakdown;
  /** Top-line composite score 0..1, used as the headline. */
  totalScore: number;
}

const FACTOR_WEIGHTS: Record<keyof Omit<ScoreBreakdown, "industry_aligned">, number> = {
  skills: 0.35,
  title_family: 0.25,
  industry: 0.20,
  years: 0.08,
  education: 0.07,
  certifications: 0.05,
};

const FACTOR_LABELS: Record<keyof Omit<ScoreBreakdown, "industry_aligned">, string> = {
  skills: "Skills",
  title_family: "Title family",
  industry: "Industry",
  years: "Experience",
  education: "Education",
  certifications: "Certifications",
};

function FactorBar({
  label,
  value,
  weight,
}: {
  label: string;
  value: number;
  weight: number;
}) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  const contribution = value * weight;
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between text-xs">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground tabular-nums">
          {value.toFixed(2)} × {weight.toFixed(2)} = {contribution.toFixed(3)}
        </span>
      </div>
      <div
        className="h-1.5 w-full rounded-full bg-muted"
        role="progressbar"
        aria-valuenow={Math.round(pct)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label} score`}
      >
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ScoreBreakdownPanel({
  breakdown,
  totalScore,
}: ScoreBreakdownPanelProps) {
  const [open, setOpen] = useState(false);

  const factors = Object.keys(FACTOR_LABELS) as Array<keyof typeof FACTOR_LABELS>;
  const totalContribution = factors.reduce(
    (sum, k) => sum + (breakdown[k] ?? 0) * FACTOR_WEIGHTS[k],
    0,
  );

  return (
    <div className="text-left">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-md border border-border bg-muted/40 px-3 py-2 text-xs font-medium hover:bg-muted/70"
        aria-expanded={open}
      >
        <span>
          Why this match? ({Math.round(totalScore * 100)}%)
        </span>
        {open ? (
          <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
        )}
      </button>

      {open && (
        <div className="mt-2 space-y-2 rounded-md border border-border bg-background p-3">
          {factors.map((factor) => (
            <FactorBar
              key={factor}
              label={FACTOR_LABELS[factor]}
              value={breakdown[factor] ?? 0}
              weight={FACTOR_WEIGHTS[factor]}
            />
          ))}

          <div className="border-t border-border pt-2 text-xs">
            <div className="flex items-baseline justify-between">
              <span className="font-medium">Composite</span>
              <span className="tabular-nums text-primary font-semibold">
                {totalContribution.toFixed(3)}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">
              {breakdown.industry_aligned
                ? "Industry-aligned: your background and this role share an industry."
                : "Industry mismatch dampener applied — your inferred industries differ from this role's."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
