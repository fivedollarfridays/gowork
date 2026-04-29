"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PROGRAM_LABELS, formatDollar } from "@/lib/constants";
import type { CliffAnalysis } from "@/lib/types";

/**
 * T-Render.6 — Drama scale.
 *
 * Stroke width 4 (was 2) so the line reads at a glance against the dark
 * gradient. The cliff threshold gets an unambiguous "← Cliff" label in
 * rose so the user's eye lands on the moment of failure. The Area's fill
 * is now a linear-gradient that ramps cool→hot horizontally, so the
 * cliff zone visually "heats up" without depending on the temperature-
 * multiplier wiring (which the polish-audit driver owns).
 */
const AREA_STROKE_WIDTH = 4;
const CLIFF_ANNOTATION = "← Cliff";
const CLIFF_GRADIENT_ID = "benefits-cliff-fill-ramp";

interface BenefitsCliffChartProps {
  analysis: CliffAnalysis | null;
}

/**
 * W3 Driver D — Wave 4: temperature-aware stroke color.
 *
 * The Wall's `--accent-current` token interpolates between cyan (cool)
 * and rose (hot) via the `--temperature-multiplier` formula in
 * `app/styles/tokens/colors.css`:
 *   --accent-current: color-mix(in oklch, --accent-cyan,
 *                               --accent-rose calc((mult - 1) * 100%))
 *
 * Ch6's wage slider drives `--temperature-multiplier` on the chapter root
 * (scope-respecting via setTemperatureMultiplier). When the cliff chart
 * paints its area-stroke as `var(--accent-current)`, the stroke
 * automatically reads cool at low wages, hot at cliff wages.
 *
 * For /plan's standalone usage (where --temperature-multiplier defaults
 * to 1.0 root-wide), this resolves to the cool cyan token — the existing
 * brand-color baseline. So the change is additive: Ch6 gets temperature
 * response, /plan stays visually identical.
 */
const STROKE_TEMPERATURE_AWARE = "var(--accent-current)";
const FILL_TEMPERATURE_AWARE =
  "color-mix(in oklch, var(--accent-current) 12%, transparent)";

function buildSummary(analysis: CliffAnalysis): string {
  if (analysis.cliff_points.length === 0) {
    return "No significant benefits cliff detected at any wage level.";
  }
  const worst = analysis.cliff_points.reduce((a, b) =>
    b.monthly_loss > a.monthly_loss ? b : a,
  );
  const program = PROGRAM_LABELS[worst.lost_program] ?? worst.lost_program;
  let text = `Your biggest cliff is at $${worst.hourly_wage}/hr where you lose $${Math.round(worst.monthly_loss)}/mo in ${program}.`;
  if (analysis.recovery_wage) {
    text += ` Net income recovers at $${analysis.recovery_wage}/hr.`;
  } else {
    text += ` Net income does not fully recover within the analyzed wage range.`;
  }
  return text;
}

export function BenefitsCliffChart({ analysis }: BenefitsCliffChartProps) {
  if (!analysis) return null;

  const summary = buildSummary(analysis);
  const cliffWages = new Set(analysis.cliff_points.map((c) => c.hourly_wage));

  const data = analysis.wage_steps.map((step) => ({
    wage: step.wage,
    net: Math.round(step.net_monthly),
    isCliff: cliffWages.has(step.wage),
  }));

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold text-primary">Benefits Cliff Analysis</h2>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">
            Net Income vs. Hourly Wage
          </CardTitle>
          <p className="text-sm text-muted-foreground">{summary}</p>
        </CardHeader>
        <CardContent>
          <div
            role="img"
            aria-label={`Benefits cliff chart. ${summary}`}
            className="w-full"
          >
            <ResponsiveContainer width="100%" height={360}>
              <AreaChart data={data} margin={{ top: 32, right: 16, left: 0, bottom: 24 }}>
                <defs>
                  {/* T-Render.6 — gradient fill ramp: cool cyan on the
                   *  left (low wages, no cliff yet) → hot rose on the
                   *  right (cliff zone). Reads dramatically without
                   *  needing the temperature-multiplier in scope. */}
                  <linearGradient id={CLIFF_GRADIENT_ID} x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity={0.35} />
                    <stop offset="55%" stopColor="var(--accent-amber)" stopOpacity={0.32} />
                    <stop offset="100%" stopColor="var(--accent-rose)" stopOpacity={0.45} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis
                  dataKey="wage"
                  tickFormatter={(v: number) => `$${v}`}
                  fontSize={12}
                  label={{ value: "Hourly Wage", position: "insideBottom", offset: -5, fontSize: 12 }}
                />
                <YAxis
                  tickFormatter={(v: number) => formatDollar(v)}
                  fontSize={12}
                  width={65}
                />
                <Tooltip
                  formatter={(value) => [formatDollar(Number(value)), "Net Monthly"]}
                  labelFormatter={(label) => `$${label}/hr`}
                />
                <Area
                  type="monotone"
                  dataKey="net"
                  stroke={STROKE_TEMPERATURE_AWARE}
                  fill={`url(#${CLIFF_GRADIENT_ID})`}
                  strokeWidth={AREA_STROKE_WIDTH}
                  activeDot={{ r: 6, strokeWidth: 2 }}
                />
                {/* Current income reference line */}
                <ReferenceLine
                  y={analysis.current_net_monthly}
                  stroke="hsl(var(--muted-foreground))"
                  strokeDasharray="6 4"
                  label={{ value: "Current", position: "right", fontSize: 11 }}
                />
                {/* Cliff zone markers — annotated unambiguously. */}
                {analysis.cliff_points.map((cliff, idx) => (
                  <ReferenceLine
                    key={`cliff-${cliff.hourly_wage}-${cliff.lost_program}`}
                    x={cliff.hourly_wage}
                    stroke="var(--accent-rose, hsl(0 84% 60%))"
                    strokeWidth={2.5}
                    strokeDasharray="4 2"
                    label={{
                      value: idx === 0 ? CLIFF_ANNOTATION : `−$${Math.round(cliff.monthly_loss)}`,
                      position: "top",
                      fontSize: 12,
                      fontWeight: 700,
                      fill: "var(--accent-rose, hsl(0 84% 60%))",
                    }}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
