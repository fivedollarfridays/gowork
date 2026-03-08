"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { JobMatchCard } from "./JobMatchCard";
import type { CreditAssessmentResult, ScoredJobMatch } from "@/lib/types";

interface JobListSectionProps {
  jobs: ScoredJobMatch[];
  pageSize?: number;
  creditResult?: CreditAssessmentResult | null;
}

export function JobListSection({ jobs, pageSize = 10, creditResult }: JobListSectionProps) {
  const [displayCount, setDisplayCount] = useState(pageSize);

  if (jobs.length === 0) return null;

  const visible = jobs.slice(0, displayCount);
  const hasMore = displayCount < jobs.length;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-primary">Matched Jobs</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {visible.map((job, i) => (
          <JobMatchCard
            key={`job-${job.title}-${job.company}-${i}`}
            job={job}
            creditResult={creditResult}
          />
        ))}
      </div>
      {hasMore ? (
        <div className="flex justify-center pt-2">
          <Button
            variant="outline"
            onClick={() => setDisplayCount((c) => c + pageSize)}
          >
            Show More Jobs ({jobs.length - displayCount} remaining)
          </Button>
        </div>
      ) : (
        <p className="text-center text-sm text-muted-foreground pt-2">
          All {jobs.length} matches reviewed
        </p>
      )}
    </div>
  );
}
