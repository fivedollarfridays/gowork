import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JobMatchCard } from "../JobMatchCard";
import type { CommuteEstimate, ScoredJobMatch } from "@/lib/types";

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

  it("shows Record Review badge when not eligible", () => {
    const job = makeJob({ record_eligible: false });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText("Record Review")).toBeInTheDocument();
  });

  it("hides Record Review badge when eligible", () => {
    const job = makeJob({ record_eligible: true });
    render(<JobMatchCard job={job} />);
    expect(screen.queryByText("Record Review")).not.toBeInTheDocument();
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

describe("JobMatchCard — source label", () => {
  it("shows 'via Honest Jobs' for honestjobs source", () => {
    const job = makeJob({ source: "honestjobs" });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText(/via Honest Jobs/)).toBeInTheDocument();
  });

  it("shows 'via Indeed' for brightdata source", () => {
    const job = makeJob({ source: "brightdata:dataset" });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText(/via Indeed/)).toBeInTheDocument();
  });

  it("shows 'via JSearch' for jsearch source", () => {
    const job = makeJob({ source: "jsearch:req-123" });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText(/via JSearch/)).toBeInTheDocument();
  });

  it("hides source label for unknown source", () => {
    const job = makeJob({ source: "test" });
    render(<JobMatchCard job={job} />);
    expect(screen.queryByText(/via /)).not.toBeInTheDocument();
  });

  it("hides source label when source is null", () => {
    const job = makeJob({ source: null });
    render(<JobMatchCard job={job} />);
    expect(screen.queryByText(/via /)).not.toBeInTheDocument();
  });
});

describe("JobMatchCard — commute estimate", () => {
  const fullCommute: CommuteEstimate = {
    drive_min: 12,
    transit_min: 25,
    walk_min: 40,
  };

  it("shows drive time when commute_estimate present", () => {
    const job = makeJob({ commute_estimate: fullCommute });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText("12 min drive")).toBeInTheDocument();
  });

  it("shows transit time when transit_min present", () => {
    const job = makeJob({ commute_estimate: fullCommute });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText("25 min transit")).toBeInTheDocument();
  });

  it("shows walk time when walk_min present", () => {
    const job = makeJob({ commute_estimate: fullCommute });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText("40 min walk")).toBeInTheDocument();
  });

  it("hides transit when transit_min is null", () => {
    const job = makeJob({
      commute_estimate: { drive_min: 15, transit_min: null, walk_min: null },
    });
    render(<JobMatchCard job={job} />);
    expect(screen.getByText("15 min drive")).toBeInTheDocument();
    expect(screen.queryByText(/min transit/)).not.toBeInTheDocument();
    expect(screen.queryByText(/min walk/)).not.toBeInTheDocument();
  });

  it("hides commute section when commute_estimate is undefined", () => {
    const job = makeJob();
    render(<JobMatchCard job={job} />);
    expect(screen.queryByText(/min drive/)).not.toBeInTheDocument();
  });

  it("hides commute section when commute_estimate is null", () => {
    const job = makeJob({ commute_estimate: null });
    render(<JobMatchCard job={job} />);
    expect(screen.queryByText(/min drive/)).not.toBeInTheDocument();
  });

  it("has aria-labels on commute badges", () => {
    const job = makeJob({ commute_estimate: fullCommute });
    render(<JobMatchCard job={job} />);
    expect(screen.getByLabelText("Estimated commute times")).toBeInTheDocument();
    expect(screen.getByLabelText("12 minute drive")).toBeInTheDocument();
    expect(screen.getByLabelText("25 minute transit")).toBeInTheDocument();
    expect(screen.getByLabelText("40 minute walk")).toBeInTheDocument();
  });
});
