import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { JobListSection } from "../JobListSection";
import type { ScoredJobMatch } from "@/lib/types";

function makeJob(title: string, overrides?: Partial<ScoredJobMatch>): ScoredJobMatch {
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

const manyJobs = Array.from({ length: 25 }, (_, i) => makeJob(`Job ${i + 1}`));

describe("JobListSection", () => {
  it("shows first pageSize jobs on initial render", () => {
    render(<JobListSection jobs={manyJobs} pageSize={10} />);
    expect(screen.getByText("Job 1")).toBeInTheDocument();
    expect(screen.getByText("Job 10")).toBeInTheDocument();
    expect(screen.queryByText("Job 11")).not.toBeInTheDocument();
  });

  it("shows 'Show More Jobs' button when more jobs exist", () => {
    render(<JobListSection jobs={manyJobs} pageSize={10} />);
    expect(screen.getByRole("button", { name: /show more/i })).toBeInTheDocument();
  });

  it("loads next batch on 'Show More' click", () => {
    render(<JobListSection jobs={manyJobs} pageSize={10} />);
    fireEvent.click(screen.getByRole("button", { name: /show more/i }));
    expect(screen.getByText("Job 11")).toBeInTheDocument();
    expect(screen.getByText("Job 20")).toBeInTheDocument();
    expect(screen.queryByText("Job 21")).not.toBeInTheDocument();
  });

  it("shows exhaustion message when all jobs displayed", () => {
    render(<JobListSection jobs={manyJobs} pageSize={10} />);
    // Click twice to show 20, then once more to show all 25
    fireEvent.click(screen.getByRole("button", { name: /show more/i }));
    fireEvent.click(screen.getByRole("button", { name: /show more/i }));
    expect(screen.getByText("Job 25")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /show more/i })).not.toBeInTheDocument();
    expect(screen.getByText(/all 25 matches reviewed/i)).toBeInTheDocument();
  });

  it("renders nothing when jobs list is empty", () => {
    const { container } = render(<JobListSection jobs={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("shows credit badge inline for credit-required jobs", () => {
    const creditJob = makeJob("Bank Teller", {
      credit_check_required: "required",
      eligible_now: false,
      eligible_after: "credit repair",
      bucket: "after_repair",
    });
    render(<JobListSection jobs={[creditJob]} />);
    expect(screen.getByText("Bank Teller")).toBeInTheDocument();
    expect(screen.getByText("Credit Check")).toBeInTheDocument();
  });

  it("does not show 'Show More' when all jobs fit in first page", () => {
    const fewJobs = [makeJob("Job A"), makeJob("Job B")];
    render(<JobListSection jobs={fewJobs} pageSize={10} />);
    expect(screen.queryByRole("button", { name: /show more/i })).not.toBeInTheDocument();
    expect(screen.getByText(/all 2 matches reviewed/i)).toBeInTheDocument();
  });
});
