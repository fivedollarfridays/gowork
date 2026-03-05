"use client";

import { useMemo } from "react";
import {
  AlertCircle,
  ArrowRight,
  Briefcase,
  Check,
  CreditCard,
  Shield,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { CreditAssessmentResult, ReEntryPlan, UserProfile } from "@/lib/types";

interface ComparisonViewProps {
  plan: ReEntryPlan;
  profile: UserProfile;
  creditResult?: CreditAssessmentResult | null;
}

interface ComparisonRow {
  label: string;
  now: string;
  future: string;
  nowIcon: React.ReactNode;
  futureIcon: React.ReactNode;
}

function buildRows(plan: ReEntryPlan, profile: UserProfile, creditResult?: CreditAssessmentResult | null): ComparisonRow[] {
  const rows: ComparisonRow[] = [];

  // Barriers
  const activeBarriers = plan.barriers.length;
  const highSeverity = plan.barriers.filter((b) => b.severity === "high").length;
  rows.push({
    label: "Barriers",
    now: `${activeBarriers} active${highSeverity > 0 ? ` (${highSeverity} high severity)` : ""}`,
    future: activeBarriers > 0 ? `${activeBarriers} addressed with action plans` : "No barriers identified",
    nowIcon: <AlertCircle className="h-4 w-4 text-destructive" />,
    futureIcon: <Check className="h-4 w-4 text-success" />,
  });

  // Jobs — prefer plan summary arrays; fall back to counting job_matches directly
  const eligibleNow = plan.eligible_now.length > 0
    ? plan.eligible_now.length
    : plan.job_matches.filter((j) => j.eligible_now).length;
  const eligibleAfter = plan.eligible_after_repair.length > 0
    ? plan.eligible_after_repair.length
    : plan.job_matches.filter((j) => !j.eligible_now).length + eligibleNow;
  rows.push({
    label: "Job Matches",
    now: `${eligibleNow} eligible now`,
    future: `${eligibleAfter} eligible after plan completion`,
    nowIcon: <Briefcase className="h-4 w-4 text-muted-foreground" />,
    futureIcon: <Briefcase className="h-4 w-4 text-success" />,
  });

  // Credit
  if (profile.needs_credit_assessment) {
    const ficoNow = creditResult?.readiness.fico_score ?? null;
    const fairThreshold = creditResult?.thresholds.find((t) => t.threshold_name === "Fair Credit") ?? null;
    const eligibleCount = creditResult
      ? creditResult.eligibility.filter((e) => e.status === "eligible").length
      : 0;
    const totalProducts = creditResult ? creditResult.eligibility.length : 0;

    const nowText = creditResult
      ? `FICO ${ficoNow} (${creditResult.readiness.score_band}) — ${eligibleCount}/${totalProducts} products eligible`
      : plan.credit_readiness_score != null
        ? `Readiness: ${plan.credit_readiness_score}/100`
        : "Assessment needed";

    rows.push({
      label: "Credit Status",
      now: nowText,
      future: fairThreshold && !fairThreshold.already_met
        ? `Fair credit (${fairThreshold.threshold_score}+) in ~${Math.round(fairThreshold.estimated_days / 30)} months — more employers accessible`
        : creditResult
          ? `${totalProducts} financial products accessible`
          : "Credit repair plan in progress — more employers accessible",
      nowIcon: <CreditCard className="h-4 w-4 text-warning-foreground" />,
      futureIcon: <CreditCard className="h-4 w-4 text-success" />,
    });
  }

  // Transit
  if (profile.transit_dependent) {
    const routeCount = plan.barriers
      .flatMap((b) => b.transit_matches)
      .reduce((set, t) => set.add(t.route_number), new Set<number>()).size;
    rows.push({
      label: "Transit Access",
      now: "Transit dependent — limited schedule",
      future: routeCount > 0 ? `${routeCount} bus route${routeCount > 1 ? "s" : ""} mapped to resources & jobs` : "Transit routes identified",
      nowIcon: <Shield className="h-4 w-4 text-muted-foreground" />,
      futureIcon: <TrendingUp className="h-4 w-4 text-success" />,
    });
  }

  return rows;
}

export function ComparisonView({ plan, profile, creditResult }: ComparisonViewProps) {
  const rows = useMemo(() => buildRows(plan, profile, creditResult), [plan, profile, creditResult]);

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold text-primary">What Changes in 3 Months</h2>

      {/* Side-by-side on desktop, stacked on mobile */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Today */}
        <Card className="border-muted bg-muted/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-muted-foreground">Today</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {rows.map((row) => (
              <div key={row.label} className="flex items-start gap-3">
                <div className="mt-0.5 shrink-0">{row.nowIcon}</div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{row.label}</p>
                  <p className="text-sm text-muted-foreground/80">{row.now}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Future */}
        <Card className="border-secondary/30 bg-secondary/5">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <CardTitle className="text-base text-secondary">In 3 Months</CardTitle>
              <Badge variant="secondary" className="text-xs">Projected</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {rows.map((row) => (
              <div key={row.label} className="flex items-start gap-3">
                <div className="mt-0.5 shrink-0">{row.futureIcon}</div>
                <div>
                  <p className="text-sm font-medium text-foreground">{row.label}</p>
                  <p className="text-sm text-foreground/80">{row.future}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Arrow indicator for mobile (between stacked cards) */}
      <div className="flex justify-center md:hidden">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <ArrowRight className="h-4 w-4" />
          <span>Follow your plan to get here</span>
        </div>
      </div>
    </section>
  );
}
