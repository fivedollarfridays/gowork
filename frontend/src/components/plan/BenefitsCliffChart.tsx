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

interface BenefitsCliffChartProps {
  analysis: CliffAnalysis | null;
}

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
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={data} margin={{ top: 20, right: 10, left: 0, bottom: 20 }}>
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
                  stroke="hsl(var(--primary))"
                  fill="hsl(var(--primary) / 0.1)"
                  strokeWidth={2}
                />
                {/* Current income reference line */}
                <ReferenceLine
                  y={analysis.current_net_monthly}
                  stroke="hsl(var(--muted-foreground))"
                  strokeDasharray="6 4"
                  label={{ value: "Current", position: "right", fontSize: 11 }}
                />
                {/* Cliff zone markers */}
                {analysis.cliff_points.map((cliff) => (
                  <ReferenceLine
                    key={`cliff-${cliff.hourly_wage}-${cliff.lost_program}`}
                    x={cliff.hourly_wage}
                    stroke="hsl(0 84% 60%)"
                    strokeDasharray="4 2"
                    label={{
                      value: `−$${Math.round(cliff.monthly_loss)}`,
                      position: "top",
                      fontSize: 11,
                      fill: "hsl(0 84% 60%)",
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
