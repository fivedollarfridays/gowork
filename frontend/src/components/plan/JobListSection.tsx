"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { JobMatchCard } from "./JobMatchCard";
import { JobFilters } from "./JobFilters";
import { JobFilterPills } from "./JobFilterPills";
import { defaultFilters, filterJobs, activeFilterCount } from "@/lib/jobFilters";
import type { JobFilterState } from "@/lib/jobFilters";
import type { CreditAssessmentResult, ScoredJobMatch } from "@/lib/types";

interface JobListSectionProps {
  jobs: ScoredJobMatch[];
  pageSize?: number;
  creditResult?: CreditAssessmentResult | null;
}

export function JobListSection({ jobs, pageSize = 10, creditResult }: JobListSectionProps) {
  const [displayCount, setDisplayCount] = useState(pageSize);
  const [filters, setFilters] = useState<JobFilterState>(defaultFilters);

  const handleFilterChange = (next: JobFilterState) => {
    setFilters(next);
    setDisplayCount(pageSize);
  };

  const filtered = useMemo(() => filterJobs(jobs, filters), [jobs, filters]);
  const filtersActive = activeFilterCount(filters) > 0;

  if (jobs.length === 0) return null;

  const visible = filtered.slice(0, displayCount);
  const hasMore = displayCount < filtered.length;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-primary">
        Matched Jobs
        {filtersActive && (
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            ({filtered.length} of {jobs.length})
          </span>
        )}
      </h2>
      <JobFilters filters={filters} onChange={handleFilterChange} />
      <JobFilterPills filters={filters} onClear={handleFilterChange} />
      {filtered.length === 0 ? (
        <p className="text-center text-sm text-muted-foreground py-6">
          No jobs match your current filters. Try adjusting or clearing filters.
        </p>
      ) : (
        <>
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
                Show More Jobs ({filtered.length - displayCount} remaining)
              </Button>
            </div>
          ) : (
            <p className="text-center text-sm text-muted-foreground pt-2">
              All {filtered.length} matches reviewed
            </p>
          )}
        </>
      )}
    </div>
  );
}
