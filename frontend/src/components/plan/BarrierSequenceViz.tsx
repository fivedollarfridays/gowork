"use client";

import { ArrowDown, Unlock, CheckCircle2, AlertTriangle, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { t } from "@/lib/i18n";

export interface SequenceStep {
  order: number;
  barrier_id: string;
  barrier_name: string;
  category: string;
  playbook: string;
  unlocks: string[];
  estimated_weeks?: number;
}

export interface BarrierSequenceData {
  steps: SequenceStep[];
  total_barriers: number;
  has_cycles: boolean;
  estimated_total_weeks?: number;
}

interface Props {
  sequence: BarrierSequenceData;
}

const CATEGORY_COLORS: Record<string, string> = {
  legal: "bg-destructive/10 text-destructive",
  financial: "bg-warning/10 text-warning-foreground",
  family: "bg-secondary/10 text-secondary",
  education: "bg-primary/10 text-primary",
  health: "bg-success/10 text-success",
  logistics: "bg-muted text-muted-foreground",
};

function humanizeId(id: string): string {
  return id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function StepCard({ step, isLast }: { step: SequenceStep; isLast: boolean }) {
  const colorClass = CATEGORY_COLORS[step.category] ?? "bg-gray-100 text-gray-800";

  return (
    <div
      className="flex flex-col items-center"
      role="listitem"
      aria-label={`Step ${step.order}: ${step.barrier_name}`}
    >
      <div className="flex items-start gap-3 w-full max-w-md">
        {/* Step number circle */}
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center text-sm font-bold">
          {step.order}
        </div>

        <div className="flex-1 space-y-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-foreground">{step.barrier_name}</span>
            <Badge variant="outline" className={`text-xs ${colorClass}`}>
              {step.category}
            </Badge>
          </div>

          {step.playbook && (
            <p className="text-sm text-muted-foreground">{step.playbook}</p>
          )}

          {step.estimated_weeks != null && step.estimated_weeks > 0 && (
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              ~{step.estimated_weeks} weeks
            </p>
          )}

          {step.unlocks.length > 0 && (
            <p className="text-xs text-secondary flex items-center gap-1">
              <Unlock className="h-3 w-3" />
              {t("sequence.unlocks")}: {step.unlocks.map(humanizeId).join(", ")}
            </p>
          )}
        </div>
      </div>

      {/* Arrow between steps */}
      {!isLast && (
        <ArrowDown className="h-5 w-5 text-muted-foreground my-2" aria-hidden="true" />
      )}
    </div>
  );
}

export function BarrierSequenceViz({ sequence }: Props) {
  if (sequence.steps.length === 0) {
    return (
      <Card>
        <CardContent className="py-6 text-center">
          <CheckCircle2 className="h-8 w-8 text-success mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            {t("sequence.noBarriers")}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          Barrier Resolution Order
          {sequence.has_cycles && (
            <AlertTriangle className="h-4 w-4 text-warning" aria-label="Cycle detected" />
          )}
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Resolve barriers in this order to maximize cascading benefits
        </p>
        {sequence.estimated_total_weeks != null && sequence.estimated_total_weeks > 0 && (
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
            <Clock className="h-3 w-3" />
            Estimated total: ~{sequence.estimated_total_weeks} weeks
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-1" role="list" aria-label="Barrier resolution steps">
          {sequence.steps.map((step, i) => (
            <StepCard
              key={step.barrier_id}
              step={step}
              isLast={i === sequence.steps.length - 1}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
