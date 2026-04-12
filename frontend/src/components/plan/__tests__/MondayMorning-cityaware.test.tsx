import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MondayMorning } from "../MondayMorning";
import type { ReEntryPlan, UserProfile } from "@/lib/types";

// Mock useCityConfig for Fort Worth
vi.mock("@/hooks/useCityConfig", () => ({
  useCityConfig: () => ({
    name: "Fort Worth",
    state: "TX",
    location: "Fort Worth, TX",
    zip_ranges: ["76101-76199"],
    loading: false,
  }),
}));

const PLAN: ReEntryPlan = {
  plan_id: "plan-fw-001",
  session_id: "test-123",
  resident_summary: null,
  barriers: [],
  job_matches: [],
  strong_matches: [],
  possible_matches: [],
  after_repair: [],
  immediate_next_steps: [],
  credit_readiness_score: null,
  eligible_now: [],
  eligible_after_repair: [],
  wioa_eligibility: null,
  job_readiness: null,
};

const PROFILE: UserProfile = {
  session_id: "test-123",
  zip_code: "76102",
  employment_status: "unemployed",
  barrier_count: 2,
  primary_barriers: ["credit", "transportation"],
  barrier_severity: "medium",
  needs_credit_assessment: true,
  transit_dependent: true,
  schedule_type: "daytime",
  work_history: "3 years retail",
  target_industries: [],
  record_profile: null,
};

describe("MondayMorning city-aware (TX)", () => {
  it("renders Fort Worth city label in subtitle", () => {
    render(<MondayMorning plan={PLAN} profile={PROFILE} />);
    // Multiple elements may contain "Fort Worth" - just verify at least one exists
    const matches = screen.getAllByText(/Fort Worth/);
    expect(matches.length).toBeGreaterThanOrEqual(1);
    // Specifically check the subtitle contains the city label
    const subtitle = screen.getByText(/Your personalized action plan for/);
    expect(subtitle.textContent).toContain("Fort Worth, TX");
  });

  it("does NOT render Montgomery in subtitle", () => {
    render(<MondayMorning plan={PLAN} profile={PROFILE} />);
    expect(screen.queryByText(/Montgomery, AL/)).not.toBeInTheDocument();
  });

  it("renders Fort Worth career center address", () => {
    render(<MondayMorning plan={PLAN} profile={PROFILE} />);
    // Workforce Solutions for Tarrant County address
    const links = screen.getAllByRole("link");
    const addressLink = links.find((l) => l.textContent?.includes("Fort Worth"));
    expect(addressLink).toBeDefined();
  });
});
