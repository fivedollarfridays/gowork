"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { daysToMonths } from "@/lib/constants";
import type { ReadinessPathwayStep } from "@/lib/types";

interface CareerPathwayProps {
  steps: ReadinessPathwayStep[];
  estimatedDays: number;
}

export function CareerPathway({ steps, estimatedDays }: CareerPathwayProps) {
  if (steps.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Career Pathway</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <ol className="space-y-3">
          {steps.map((step) => (
            <li key={step.step_number} className="flex gap-3 text-sm">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-secondary/10 text-secondary text-xs font-semibold">
                {step.step_number}
              </span>
              <div>
                <span className="font-medium">{step.action}</span>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {step.resource} &middot; {daysToMonths(step.timeline_days)}
                </p>
              </div>
            </li>
          ))}
        </ol>
        {estimatedDays > 0 && (
          <p className="text-xs text-muted-foreground pt-1 border-t">
            Estimated time to ready: {daysToMonths(estimatedDays)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
