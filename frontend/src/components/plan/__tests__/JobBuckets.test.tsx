import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JobMatchCard } from "../JobMatchCard";
import { JobBucketSection } from "../JobBucketSection";
import type { ScoredJobMatch } from "@/lib/types";

const strongJob: ScoredJobMatch = {
  title: "Certified Nursing Assistant",
  company: "Baptist Health",
  location: "Montgomery, AL",
  url: "https://example.com",
  source: "seed",
  transit_accessible: true,
  route: null,
  credit_check_required: "not_required",
  eligible_now: true,
  eligible_after: null,
  relevance_score: 0.85,
  match_reason: "Matches your CNA experience",
  bucket: "strong",
};

const afterRepairJob: ScoredJobMatch = {
  title: "Bank Teller",
  company: "Regions",
  location: "Montgomery, AL",
  url: null,
  source: "seed",
  transit_accessible: true,
  route: null,
  credit_check_required: "required",
  eligible_now: false,
  eligible_after: "credit repair",
  relevance_score: 0.5,
  match_reason: "Matches your target industry",
  bucket: "after_repair",
};

describe("JobMatchCard with ScoredJobMatch", () => {
  it("displays match_reason for scored jobs", () => {
    render(<JobMatchCard job={strongJob} />);
    expect(screen.getByText("Matches your CNA experience")).toBeInTheDocument();
  });

  it("displays relevance score badge for strong matches", () => {
    render(<JobMatchCard job={strongJob} />);
    expect(screen.getByText("85% Match")).toBeInTheDocument();
  });

  it("displays credit badge for credit-required jobs", () => {
    render(<JobMatchCard job={afterRepairJob} />);
    expect(screen.getByText("Credit Check")).toBeInTheDocument();
  });

  it("displays green pay badge when pay_range is present", () => {
    render(<JobMatchCard job={{ ...strongJob, pay_range: "$15.00/hr" }} />);
    expect(screen.getByText("$15.00/hr")).toBeInTheDocument();
  });

  it("displays amber 'Pay not disclosed' badge when pay_range is null", () => {
    render(<JobMatchCard job={{ ...strongJob, pay_range: null }} />);
    expect(screen.getByText("Pay not disclosed")).toBeInTheDocument();
  });

  it("displays amber badge when pay_range is undefined", () => {
    render(<JobMatchCard job={strongJob} />);
    expect(screen.getByText("Pay not disclosed")).toBeInTheDocument();
  });
});

const possibleJob: ScoredJobMatch = {
  title: "Warehouse Associate",
  company: "Target",
  location: "Montgomery, AL",
  url: null,
  source: "seed",
  transit_accessible: true,
  route: null,
  credit_check_required: "not_required",
  eligible_now: true,
  eligible_after: null,
  relevance_score: 0.45,
  match_reason: "Entry-level opportunity",
  bucket: "possible",
};

describe("JobBucketSection", () => {
  it("renders heading and jobs when list is non-empty", () => {
    render(
      <JobBucketSection title="Strong Matches" jobs={[strongJob]} />,
    );
    expect(screen.getByText("Strong Matches")).toBeInTheDocument();
    expect(screen.getByText("Certified Nursing Assistant")).toBeInTheDocument();
  });

  it("renders nothing when jobs list is empty", () => {
    const { container } = render(
      <JobBucketSection title="Strong Matches" jobs={[]} />,
    );
    expect(screen.queryByText("Strong Matches")).not.toBeInTheDocument();
    expect(container.innerHTML).toBe("");
  });

  it("renders description when provided", () => {
    render(
      <JobBucketSection
        title="After Credit Repair"
        jobs={[afterRepairJob]}
        description="These jobs require credit repair first."
      />,
    );
    expect(screen.getByText("These jobs require credit repair first.")).toBeInTheDocument();
  });
});
