/**
 * Ch6 (The Math) helpers — kept here so `Chapter06TheMath.tsx` stays
 * under arch-check function/import limits.
 *
 * # Demo cliff analysis
 *
 * The chapter ships a STATIC analysis derived from Carlos's profile so
 * the cliff is visible even before the API is wired in. Numbers are a
 * representative projection (single father, 1 dependent, 76119, no
 * child support) and match the EditorialCliff fixture used in
 * BenefitsCliffChart's existing tests.
 *
 * W4 polish can swap this for a live `/api/cliff-analysis?profile=...`
 * fetch — the chart accepts the same shape either way.
 *
 * # Honest uncertainty (C4)
 *
 * The wage range, monthly losses, and recovery wage were lifted from
 * the demo seed at `data/demo/ronnetta_demo_state.json` (closest
 * comparable profile shipped by the team). Carlos's exact cliff curve
 * may differ once the cliff calculator runs against his real intake.
 */

import type { CliffAnalysis } from "@/lib/types";

/** Default position for the wage slider — middle-of-cliff $15/hr. */
export const WAGE_SLIDER_DEFAULT = 15 as const;

/** Slider step size — half-dollar resolution makes the cliff legible. */
export const WAGE_SLIDER_STEP = 0.5 as const;

/** Format USD/hr for the slider value label. */
export function formatWageUsd(wage: number): string {
  return `$${wage.toFixed(2)}/hr`;
}

/**
 * Carlos's representative cliff analysis. 7-step wage curve with two
 * cliffs: childcare subsidy at $14/hr + SNAP at $17/hr.
 */
export const CARLOS_DEMO_CLIFF_ANALYSIS: CliffAnalysis = {
  wage_steps: [
    { wage: 7.25, gross_monthly: 1257, benefits_total: 1480, net_monthly: 2737 },
    { wage: 10.0, gross_monthly: 1733, benefits_total: 1340, net_monthly: 3073 },
    { wage: 12.5, gross_monthly: 2167, benefits_total: 1180, net_monthly: 3347 },
    { wage: 14.0, gross_monthly: 2427, benefits_total: 600, net_monthly: 3027 },
    { wage: 17.0, gross_monthly: 2947, benefits_total: 240, net_monthly: 3187 },
    { wage: 20.0, gross_monthly: 3467, benefits_total: 0, net_monthly: 3467 },
    { wage: 25.0, gross_monthly: 4333, benefits_total: 0, net_monthly: 4333 },
  ],
  cliff_points: [
    {
      hourly_wage: 14.0,
      annual_income: 29120,
      net_monthly_income: 3027,
      lost_program: "ccdf",
      monthly_loss: 580,
      severity: "severe",
    },
    {
      hourly_wage: 17.0,
      annual_income: 35360,
      net_monthly_income: 3187,
      lost_program: "snap",
      monthly_loss: 360,
      severity: "moderate",
    },
  ],
  current_net_monthly: 2737,
  programs: [
    { program: "snap", monthly_value: 540, eligible: true },
    { program: "ccdf", monthly_value: 800, eligible: true },
    { program: "medicaid", monthly_value: 140, eligible: true },
  ],
  worst_cliff_wage: 14.0,
  recovery_wage: 20.0,
};
