import type { ScoredJobMatch } from "@/lib/types";

export interface JobFilterState {
  source: "all" | "brightdata" | "jsearch" | "honestjobs";
  fairChanceOnly: boolean;
  schedule: "all" | "full-time" | "part-time";
}

export const SOURCE_LABELS: Record<string, string> = {
  brightdata: "BrightData",
  jsearch: "JSearch",
  honestjobs: "Honest Jobs",
};

export const SCHEDULE_LABELS: Record<string, string> = {
  "full-time": "Full-time",
  "part-time": "Part-time",
};

export const defaultFilters: JobFilterState = {
  source: "all",
  fairChanceOnly: false,
  schedule: "all",
};

function matchesSource(job: ScoredJobMatch, source: string): boolean {
  if (source === "all") return true;
  const jobSource = job.source ?? "";
  if (source === "brightdata") return jobSource.startsWith("brightdata:");
  if (source === "jsearch") return jobSource.startsWith("jsearch:");
  return jobSource === source;
}

function matchesSchedule(job: ScoredJobMatch, schedule: string): boolean {
  if (schedule === "all") return true;
  const empType = (job.employment_type ?? "").toUpperCase();
  if (schedule === "full-time") return empType === "FULLTIME";
  if (schedule === "part-time") return empType === "PARTTIME";
  return true;
}

export function filterJobs(
  jobs: ScoredJobMatch[],
  filters: JobFilterState,
): ScoredJobMatch[] {
  return jobs.filter((job) => {
    if (!matchesSource(job, filters.source)) return false;
    if (filters.fairChanceOnly && !job.fair_chance) return false;
    if (!matchesSchedule(job, filters.schedule)) return false;
    return true;
  });
}

export function activeFilterCount(filters: JobFilterState): number {
  let count = 0;
  if (filters.source !== "all") count++;
  if (filters.fairChanceOnly) count++;
  if (filters.schedule !== "all") count++;
  return count;
}
