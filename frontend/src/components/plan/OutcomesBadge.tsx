"use client";

import { useQuery } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { getAggregateOutcomes } from "@/lib/api";

/**
 * Displays aggregate outcome stats on the landing page.
 * Shows assessment count and improvement messaging.
 */
export function OutcomesBadge() {
  const { data, isLoading } = useQuery({
    queryKey: ["outcomes-aggregate"],
    queryFn: getAggregateOutcomes,
    staleTime: 60_000,
  });

  if (isLoading || !data || data.assessment_count === 0) return null;

  return (
    <div className="flex items-center gap-2 rounded-lg border border-secondary/20 bg-secondary/5 px-4 py-2 text-sm">
      <Users className="h-4 w-4 text-secondary shrink-0" />
      <span>
        <strong>{data.assessment_count}</strong> assessments completed
        {data.top_barriers.length > 0 && (
          <span className="text-muted-foreground">
            {" "} -- barrier intelligence improving recommendations
          </span>
        )}
      </span>
    </div>
  );
}
