"use client";

import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { READINESS_BAND_STYLES, humanizeLabel } from "@/lib/constants";
import { CareerPathway } from "@/components/plan/CareerPathway";
import type { JobReadinessResult } from "@/lib/types";

interface JobReadinessResultsProps {
  result: JobReadinessResult;
}

function weightLabel(weight: number): string {
  return `${Math.round(weight * 100)}%`;
}

export function JobReadinessResults({ result }: JobReadinessResultsProps) {
  const bandStyle = READINESS_BAND_STYLES[result.readiness_band] ?? READINESS_BAND_STYLES.developing;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Activity className="h-5 w-5 text-foreground/70" />
              </div>
              <div>
                <CardTitle className="text-base">Job Readiness Score</CardTitle>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {result.overall_score}/100
                </p>
              </div>
            </div>
            <Badge
              variant="outline"
              className={cn("capitalize", bandStyle.bg, bandStyle.text, bandStyle.border)}
            >
              {humanizeLabel(result.readiness_band)}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* Overall Score */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Overall Readiness</span>
              <span className="font-semibold">{result.overall_score}/100</span>
            </div>
            <Progress value={result.overall_score} className="h-2" />
          </div>

          {/* Factor Breakdown */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Factor Breakdown</h4>
            <div className="space-y-2">
              {result.factors.map((factor) => (
                <div key={factor.name} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">
                      {factor.name}{" "}
                      <span className="opacity-60">({weightLabel(factor.weight)})</span>
                    </span>
                    <span className="font-medium">{factor.score}/100</span>
                  </div>
                  <Progress value={factor.score} className="h-1.5" />
                </div>
              ))}
            </div>
          </div>

          {/* Summary */}
          <p className="text-sm text-muted-foreground">{result.summary}</p>
        </CardContent>
      </Card>

      <CareerPathway
        steps={result.pathway}
        estimatedDays={result.estimated_days_to_ready}
      />
    </div>
  );
}
