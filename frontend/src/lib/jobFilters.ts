import type { ScoredJobMatch } from "@/lib/types";

export type SortOption = "relevance" | "pay";

export interface JobFilterState {
  source: "all" | "brightdata" | "honestjobs";
  fairChanceOnly: boolean;
  schedule: "all" | "full-time" | "part-time";
  minPay: number;
}

export const SOURCE_LABELS: Record<string, string> = {
  brightdata: "BrightData",
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
  minPay: 0,
};

function matchesSource(job: ScoredJobMatch, source: string): boolean {
  if (source === "all") return true;
  const jobSource = job.source ?? "";
  if (source === "brightdata") return jobSource.startsWith("brightdata:");
  return jobSource === source;
}

function matchesSchedule(job: ScoredJobMatch, schedule: string): boolean {
  if (schedule === "all") return true;
  const empType = (job.employment_type ?? "").toUpperCase();
  if (schedule === "full-time") return empType === "FULLTIME";
  if (schedule === "part-time") return empType === "PARTTIME";
  return true;
}

export function parseHourlyRate(payRange: string | null | undefined): number | null {
  if (!payRange) return null;
  const match = payRange.match(/\$([0-9]+(?:\.[0-9]+)?)/);
  return match ? parseFloat(match[1]) : null;
}

export function filterJobs(
  jobs: ScoredJobMatch[],
  filters: JobFilterState,
): ScoredJobMatch[] {
  return jobs.filter((job) => {
    if (!matchesSource(job, filters.source)) return false;
    if (filters.fairChanceOnly && !job.fair_chance) return false;
    if (!matchesSchedule(job, filters.schedule)) return false;
    if (filters.minPay > 0) {
      const rate = parseHourlyRate(job.pay_range);
      if (rate === null || rate < filters.minPay) return false;
    }
    return true;
  });
}

export function sortJobs(
  jobs: ScoredJobMatch[],
  sort: SortOption,
): ScoredJobMatch[] {
  const sorted = [...jobs];
  if (sort === "pay") {
    sorted.sort((a, b) => (parseHourlyRate(b.pay_range) ?? 0) - (parseHourlyRate(a.pay_range) ?? 0));
  } else {
    sorted.sort((a, b) => b.relevance_score - a.relevance_score);
  }
  return sorted;
}

export function activeFilterCount(filters: JobFilterState): number {
  let count = 0;
  if (filters.source !== "all") count++;
  if (filters.fairChanceOnly) count++;
  if (filters.schedule !== "all") count++;
  if (filters.minPay > 0) count++;
  return count;
}
