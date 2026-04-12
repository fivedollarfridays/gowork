"use client";

import { useState, useMemo } from "react";
import { AlertTriangle, Loader2, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { formatDollar } from "@/lib/constants";
import { getTranslation, getLocale } from "@/lib/i18n";
import type { CliffAnalysis, WageStep, CliffPoint } from "@/lib/types";

interface BenefitsCliffSimulatorProps {
  analysis: CliffAnalysis | null;
  loading?: boolean;
  error?: string | null;
}

function findStep(steps: WageStep[], wage: number): WageStep | null {
  if (steps.length === 0) return null;
  let closest = steps[0];
  for (const s of steps) {
    if (Math.abs(s.wage - wage) < Math.abs(closest.wage - wage)) {
      closest = s;
    }
  }
  return closest;
}

function cliffAt(cliffs: CliffPoint[], wage: number): CliffPoint | null {
  return cliffs.find((c) => c.hourly_wage === wage) ?? null;
}

function WageDisplay({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}

function CliffWarning({ cliff }: { cliff: CliffPoint }) {
  const locale = getLocale();
  const lossLabel = getTranslation("cliffSimulator.programLoss", locale);
  return (
    <div
      role="alert"
      className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm"
    >
      <AlertTriangle className="h-4 w-4 text-destructive shrink-0" aria-hidden="true" />
      <span>
        {lossLabel}: <strong>{cliff.lost_program}</strong>{" "}
        (-{formatDollar(cliff.monthly_loss)}/mo)
      </span>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground" role="status">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
      <span>Loading cliff analysis...</span>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div role="alert" className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm">
      <AlertTriangle className="h-4 w-4 text-destructive shrink-0" aria-hidden="true" />
      <span>{message}</span>
    </div>
  );
}

export function BenefitsCliffSimulator({ analysis, loading, error }: BenefitsCliffSimulatorProps) {
  const locale = getLocale();
  const heading = getTranslation("cliffSimulator.heading", locale);
  const description = getTranslation("cliffSimulator.description", locale);
  const hourlyLabel = getTranslation("cliffSimulator.hourlyWage", locale);
  const grossLabel = getTranslation("cliffSimulator.monthlyGross", locale);
  const benefitsLabel = getTranslation("cliffSimulator.benefitsTotal", locale);
  const netLabel = getTranslation("cliffSimulator.netMonthly", locale);

  const minWage = analysis?.wage_steps[0]?.wage ?? 8;
  const maxWage = analysis?.wage_steps[analysis.wage_steps.length - 1]?.wage ?? 25;

  const [selectedWage, setSelectedWage] = useState(minWage);

  const currentStep = useMemo(
    () => (analysis ? findStep(analysis.wage_steps, selectedWage) : null),
    [analysis, selectedWage],
  );

  const activeCliff = useMemo(
    () => (analysis ? cliffAt(analysis.cliff_points, selectedWage) : null),
    [analysis, selectedWage],
  );

  if (loading) {
    return (
      <section className="space-y-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              {heading}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <LoadingState />
          </CardContent>
        </Card>
      </section>
    );
  }

  if (error) {
    return (
      <section className="space-y-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              {heading}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ErrorState message={error} />
          </CardContent>
        </Card>
      </section>
    );
  }

  if (!analysis || analysis.wage_steps.length === 0) return null;

  return (
    <section className="space-y-4" aria-label={heading}>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <TrendingUp className="h-4 w-4" aria-hidden="true" />
            {heading}
          </CardTitle>
          <p className="text-sm text-muted-foreground">{description}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Wage slider */}
          <div className="space-y-3">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>${minWage}/hr</span>
              <span className="font-semibold text-foreground text-lg" aria-live="polite">
                ${selectedWage}/hr
              </span>
              <span>${maxWage}/hr</span>
            </div>
            <Slider
              value={[selectedWage]}
              min={minWage}
              max={maxWage}
              step={1}
              onValueChange={([v]) => setSelectedWage(v)}
              aria-label={hourlyLabel}
              aria-valuemin={minWage}
              aria-valuemax={maxWage}
              aria-valuenow={selectedWage}
              aria-valuetext={`$${selectedWage} per hour`}
            />
          </div>

          {/* Metrics grid */}
          {currentStep && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 rounded-lg bg-muted/50 p-4" role="group" aria-label="Income breakdown">
              <WageDisplay label={grossLabel} value={formatDollar(currentStep.gross_monthly)} />
              <WageDisplay label={benefitsLabel} value={formatDollar(currentStep.benefits_total)} />
              <WageDisplay label={netLabel} value={formatDollar(currentStep.net_monthly)} />
            </div>
          )}

          {/* Cliff warnings */}
          {activeCliff && <CliffWarning cliff={activeCliff} />}

          {/* All cliff points summary */}
          {analysis.cliff_points.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Cliff Points
              </p>
              <div className="flex flex-wrap gap-2">
                {analysis.cliff_points.map((cp) => (
                  <span
                    key={`${cp.hourly_wage}-${cp.lost_program}`}
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs border ${
                      cp.hourly_wage === selectedWage
                        ? "bg-destructive/10 text-destructive border-destructive/30"
                        : "bg-muted text-muted-foreground border-border"
                    }`}
                  >
                    ${cp.hourly_wage}/hr: {cp.lost_program}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
