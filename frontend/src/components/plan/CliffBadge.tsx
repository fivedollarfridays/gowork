"use client";

import { AlertTriangle, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { PROGRAM_LABELS, STATUS_BADGE_STYLES } from "@/lib/constants";
import type { CliffImpact } from "@/lib/types";

function formatDollars(amount: number): string {
  const abs = Math.abs(Math.round(amount));
  const sign = amount >= 0 ? "+" : "-";
  return `${sign}$${abs}/mo`;
}

interface CliffBadgeProps {
  cliffImpact: CliffImpact | null | undefined;
}

export function CliffBadge({ cliffImpact }: CliffBadgeProps) {
  if (!cliffImpact) return null;

  if (!cliffImpact.has_cliff) {
    return (
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge
          className={`${STATUS_BADGE_STYLES.positive} text-xs`}
          variant="outline"
          aria-label={`No benefits impact, ${formatDollars(cliffImpact.net_monthly_change)} vs current`}
        >
          <ShieldCheck className="h-3 w-3 mr-1" aria-hidden="true" />
          No benefits impact
        </Badge>
        <span className="text-xs text-muted-foreground">
          {formatDollars(cliffImpact.net_monthly_change)} vs current
        </span>
      </div>
    );
  }

  const programs = cliffImpact.affected_programs
    .map((p) => PROGRAM_LABELS[p] ?? p)
    .join(", ");

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <Badge
        className={`${
          cliffImpact.severity === "severe"
            ? STATUS_BADGE_STYLES.negative
            : STATUS_BADGE_STYLES.warning
        } text-xs`}
        variant="outline"
        aria-label={`Benefits cliff warning: ${formatDollars(cliffImpact.benefits_change)}, loses ${programs || "benefits"}`}
      >
        <AlertTriangle className="h-3 w-3 mr-1" aria-hidden="true" />
        {formatDollars(cliffImpact.benefits_change)} benefits
      </Badge>
      {programs && (
        <span className="text-xs text-muted-foreground">
          Loses {programs}
        </span>
      )}
      <span className="text-xs text-muted-foreground">
        {formatDollars(cliffImpact.net_monthly_change)} vs current
      </span>
    </div>
  );
}
