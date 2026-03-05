"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  CreditCard,
  CheckCircle2,
  Clock,
  AlertTriangle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { CreditAssessmentResult } from "@/lib/types";
import { SEVERITY_BADGE_STYLES } from "@/lib/constants";

interface CreditResultsProps {
  result: CreditAssessmentResult;
}

function factorLabel(key: string): string {
  const labels: Record<string, string> = {
    payment_history: "Payment History",
    utilization: "Credit Utilization",
    credit_age: "Account Age",
    credit_mix: "Credit Mix",
    new_credit: "New Credit",
  };
  return labels[key] ?? key;
}

function factorWeight(key: string): string {
  const weights: Record<string, string> = {
    payment_history: "35%",
    utilization: "30%",
    credit_age: "15%",
    credit_mix: "10%",
    new_credit: "10%",
  };
  return weights[key] ?? "";
}

function daysToMonths(days: number): string {
  if (days <= 30) return `${days} days`;
  const months = Math.round(days / 30);
  return `~${months} month${months === 1 ? "" : "s"}`;
}

export function CreditResults({ result }: CreditResultsProps) {
  const [showDispute, setShowDispute] = useState(false);
  const [showEligibility, setShowEligibility] = useState(false);
  const { readiness, thresholds, dispute_pathway, eligibility } = result;
  const badgeStyle = SEVERITY_BADGE_STYLES[result.barrier_severity as keyof typeof SEVERITY_BADGE_STYLES] ?? SEVERITY_BADGE_STYLES.low;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
              <CreditCard className="h-5 w-5 text-foreground/70" />
            </div>
            <div>
              <CardTitle className="text-base">Credit Assessment</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                Score: {readiness.fico_score} ({readiness.score_band})
              </p>
            </div>
          </div>
          <Badge className={cn("capitalize", badgeStyle)} variant="outline">
            {result.barrier_severity}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Readiness Score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Credit Readiness</span>
            <span className="font-semibold">{readiness.score}/100</span>
          </div>
          <Progress value={readiness.score} className="h-2" />
        </div>

        {/* Key Factors */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Key Factors</h4>
          <div className="space-y-2">
            {Object.entries(readiness.factors).map(([key, value]) => (
              <div key={key} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">
                    {factorLabel(key)} <span className="opacity-60">({factorWeight(key)})</span>
                  </span>
                  <span className="font-medium">{Math.round(value * 100)}%</span>
                </div>
                <Progress value={value * 100} className="h-1.5" />
              </div>
            ))}
          </div>
        </div>

        <Separator />

        {/* Credit Thresholds */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Credit Milestones</h4>
          <div className="grid gap-2">
            {thresholds.map((t) => (
              <div
                key={t.threshold_name}
                className={cn(
                  "flex items-center justify-between rounded-lg border p-3 text-sm",
                  t.already_met ? "bg-green-50 border-green-200" : "bg-muted/30"
                )}
              >
                <div className="flex items-center gap-2">
                  {t.already_met ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                  ) : (
                    <Clock className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                  <div>
                    <span className="font-medium">{t.threshold_name}</span>
                    <span className="text-muted-foreground ml-1">({t.threshold_score}+)</span>
                  </div>
                </div>
                {t.already_met ? (
                  <Badge variant="outline" className="bg-green-100 text-green-700 border-green-200 text-xs">
                    Reached
                  </Badge>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    {daysToMonths(t.estimated_days)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Dispute Pathway */}
        {dispute_pathway.steps.length > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDispute(!showDispute)}
                className="w-full justify-between h-8 px-0 hover:bg-transparent"
              >
                <span className="text-sm font-medium flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Dispute Pathway
                  <span className="text-xs text-muted-foreground font-normal">
                    ({daysToMonths(dispute_pathway.total_estimated_days)})
                  </span>
                </span>
                {showDispute ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
              {showDispute && (
                <ol className="space-y-3 ml-1">
                  {dispute_pathway.steps.map((step) => (
                    <li key={step.step_number} className="flex gap-3 text-sm">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-secondary/10 text-secondary text-xs font-semibold">
                        {step.step_number}
                      </span>
                      <div>
                        <span className="font-medium">{step.action}</span>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {step.description}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </>
        )}

        {/* Eligibility */}
        {eligibility.length > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowEligibility(!showEligibility)}
                className="w-full justify-between h-8 px-0 hover:bg-transparent"
              >
                <span className="text-sm font-medium">
                  Product Eligibility ({eligibility.filter((e) => e.status === "eligible").length}/{eligibility.length} eligible)
                </span>
                {showEligibility ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
              {showEligibility && (
                <div className="grid gap-2">
                  {eligibility.map((e) => (
                    <div
                      key={e.product_name}
                      className={cn(
                        "flex items-center justify-between rounded-lg border p-3 text-sm",
                        e.status === "eligible" ? "bg-green-50 border-green-200" : "bg-muted/30"
                      )}
                    >
                      <div>
                        <span className="font-medium">{e.product_name}</span>
                        <span className="text-xs text-muted-foreground ml-1">({e.category})</span>
                      </div>
                      {e.status === "eligible" ? (
                        <Badge variant="outline" className="bg-green-100 text-green-700 border-green-200 text-xs">
                          Eligible
                        </Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          {e.gap_points > 0 ? `${e.gap_points} pts away` : ""} {e.estimated_days_to_eligible > 0 ? `(${daysToMonths(e.estimated_days_to_eligible)})` : ""}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {/* Disclaimer */}
        <div className="rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground italic">
          {result.disclaimer}
        </div>
      </CardContent>
    </Card>
  );
}
