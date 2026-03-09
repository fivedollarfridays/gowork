"use client";

import { TimelinePhaseCard } from "./TimelinePhaseCard";
import type { ActionPlan } from "@/lib/types";
import { formatDateRange } from "@/lib/constants";

interface ActionTimelineProps {
  actionPlan: ActionPlan | null | undefined;
  assessmentDate?: string;
  checklist?: Record<string, boolean>;
  onToggle?: (key: string, completed: boolean) => void;
}

export function ActionTimeline({ actionPlan, assessmentDate, checklist, onToggle }: ActionTimelineProps) {
  if (!actionPlan || !actionPlan.phases || actionPlan.phases.length === 0) {
    return null;
  }

  const dateBase = assessmentDate ?? actionPlan.assessment_date;
  const activePhases = actionPlan.phases.filter((p) => p.actions.length > 0);

  if (activePhases.length === 0) return null;

  return (
    <section aria-label="Action plan timeline" className="space-y-4">
      <h2 className="text-xl font-semibold text-primary">Your Action Plan Timeline</h2>
      <div className="space-y-3">
        {activePhases.map((phase, i) => (
          <TimelinePhaseCard
            key={phase.phase_id}
            phase={phase}
            dateRange={formatDateRange(dateBase, phase.start_day, phase.end_day)}
            defaultOpen={i === 0}
            checklist={checklist}
            onToggle={onToggle}
          />
        ))}
      </div>
    </section>
  );
}
