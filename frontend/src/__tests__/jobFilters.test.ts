import { describe, it, expect } from "vitest";
import type { ScoredJobMatch } from "@/lib/types";
import {
  filterJobs,
  defaultFilters,
  type JobFilterState,
} from "@/lib/jobFilters";

function makeJob(
  title: string,
  overrides?: Partial<ScoredJobMatch>,
): ScoredJobMatch {
  return {
    title,
    company: "TestCo",
    location: "Montgomery, AL",
    url: null,
    source: "seed",
    transit_accessible: true,
    route: null,
    credit_check_required: "not_required",
    eligible_now: true,
    eligible_after: null,
    relevance_score: 0.7,
    match_reason: "Entry-level opportunity",
    bucket: "strong",
    ...overrides,
  };
}

describe("filterJobs", () => {
  const jobs: ScoredJobMatch[] = [
    makeJob("CNA", { source: "brightdata:snap-1", pay_range: "$14-$18/hr" }),
    makeJob("Driver", {
      source: "jsearch:req-1",
      fair_chance: true,
      pay_range: "$20-$25/hr",
    }),
    makeJob("Cook", { source: "honestjobs", fair_chance: true }),
    makeJob("Cashier", { source: "brightdata:snap-2", pay_range: "$10-$12/hr" }),
  ];

  it("returns all jobs with default filters", () => {
    const result = filterJobs(jobs, defaultFilters);
    expect(result).toHaveLength(4);
  });

  it("filters by source: brightdata", () => {
    const filters: JobFilterState = { ...defaultFilters, source: "brightdata" };
    const result = filterJobs(jobs, filters);
    expect(result).toHaveLength(2);
    expect(result.every((j) => j.source?.startsWith("brightdata:"))).toBe(true);
  });

  it("filters by source: jsearch", () => {
    const filters: JobFilterState = { ...defaultFilters, source: "jsearch" };
    const result = filterJobs(jobs, filters);
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("Driver");
  });

  it("filters by source: honestjobs", () => {
    const filters: JobFilterState = { ...defaultFilters, source: "honestjobs" };
    const result = filterJobs(jobs, filters);
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("Cook");
  });

  it("filters by fair_chance only", () => {
    const filters: JobFilterState = {
      ...defaultFilters,
      fairChanceOnly: true,
    };
    const result = filterJobs(jobs, filters);
    expect(result).toHaveLength(2);
    expect(result.every((j) => j.fair_chance)).toBe(true);
  });

  it("filters by schedule: full-time", () => {
    const ftJob = makeJob("FT Job", { employment_type: "FULLTIME" });
    const ptJob = makeJob("PT Job", { employment_type: "PARTTIME" });
    const noType = makeJob("No Type");
    const filters: JobFilterState = { ...defaultFilters, schedule: "full-time" };
    const result = filterJobs([ftJob, ptJob, noType], filters);
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("FT Job");
  });

  it("filters by schedule: part-time", () => {
    const ftJob = makeJob("FT Job", { employment_type: "FULLTIME" });
    const ptJob = makeJob("PT Job", { employment_type: "PARTTIME" });
    const filters: JobFilterState = { ...defaultFilters, schedule: "part-time" };
    const result = filterJobs([ftJob, ptJob], filters);
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("PT Job");
  });

  it("combines source + fair_chance filters", () => {
    const filters: JobFilterState = {
      ...defaultFilters,
      source: "honestjobs",
      fairChanceOnly: true,
    };
    const result = filterJobs(jobs, filters);
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("Cook");
  });

  it("returns empty for no matches", () => {
    const filters: JobFilterState = {
      ...defaultFilters,
      source: "jsearch",
      fairChanceOnly: false,
      schedule: "part-time",
    };
    // jsearch driver has no employment_type, so part-time filter excludes it
    const result = filterJobs(jobs, filters);
    expect(result).toHaveLength(0);
  });

  it("handles empty jobs list", () => {
    const result = filterJobs([], defaultFilters);
    expect(result).toHaveLength(0);
  });
});

describe("defaultFilters", () => {
  it("has expected shape", () => {
    expect(defaultFilters).toEqual({
      source: "all",
      fairChanceOnly: false,
      schedule: "all",
    });
  });
});
