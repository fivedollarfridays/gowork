import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JobMatchCard } from "../JobMatchCard";
import type { ScoredJobMatch } from "@/lib/types";

function makeJob(overrides: Partial<ScoredJobMatch> = {}): ScoredJobMatch {
  return {
    title: "Cashier",
    company: "Store",
    location: "Montgomery, AL",
    url: "https://example.com",
    source: "test",
    transit_accessible: true,
    route: null,
    credit_check_required: "unknown",
    eligible_now: true,
    eligible_after: null,
    relevance_score: 0.75,
    match_reason: "Entry-level opportunity",
    bucket: "strong" as const,
    ...overrides,
  };
}

describe("JobMatchCard — fair-chance badge", () => {
  it("shows Fair Chance badge when fair_chance is true", () => {
    const job = makeJob({ fair_chance: true });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText("Fair Chance")).toBeInTheDocument();
  });

  it("hides Fair Chance badge when fair_chance is false", () => {
    const job = makeJob({ fair_chance: false });
    render(<JobMatchCard job={job} />);
    expect(screen.queryByText("Fair Chance")).not.toBeInTheDocument();
  });

  it("hides Fair Chance badge when fair_chance is undefined", () => {
    const job = makeJob();
    render(<JobMatchCard job={job} />);
    expect(screen.queryByText("Fair Chance")).not.toBeInTheDocument();
  });

  it("shows Record Review Needed badge when not eligible", () => {
    const job = makeJob({ record_eligible: false });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText("Record Review Needed")).toBeInTheDocument();
  });

  it("hides Record Review Needed when eligible", () => {
    const job = makeJob({ record_eligible: true });
    render(<JobMatchCard job={job} />);
    expect(screen.queryByText("Record Review Needed")).not.toBeInTheDocument();
  });

  it("shows record note when present", () => {
    const job = makeJob({ record_note: "Eligible after 3 more years" });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText("Eligible after 3 more years")).toBeInTheDocument();
  });

  it("hides record note when null", () => {
    const job = makeJob({ record_note: null });
    render(<JobMatchCard job={job} />);
    expect(screen.queryByText(/Eligible after/)).not.toBeInTheDocument();
  });
});
