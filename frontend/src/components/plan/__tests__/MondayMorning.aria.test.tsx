import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MondayMorning } from "../MondayMorning";
import type { ReEntryPlan, UserProfile } from "@/lib/types";
import { AvailableHours, EmploymentStatus } from "@/lib/types";

const basePlan: ReEntryPlan = {
  plan_id: "plan-001",
  session_id: "sess-abc",
  resident_summary: null,
  barriers: [],
  job_matches: [],
  immediate_next_steps: ["Visit career center"],
  credit_readiness_score: null,
  eligible_now: [],
  eligible_after_repair: [],
  strong_matches: [],
  possible_matches: [],
  after_repair: [],
  wioa_eligibility: null,
  job_readiness: null,
};

const baseProfile: UserProfile = {
  session_id: "sess-abc",
  zip_code: "36104",
  employment_status: EmploymentStatus.UNEMPLOYED,
  barrier_count: 0,
  primary_barriers: [],
  barrier_severity: "low",
  needs_credit_assessment: false,
  transit_dependent: false,
  schedule_type: AvailableHours.DAYTIME,
  work_history: "",
  target_industries: [],
  record_profile: null,
};

describe("MondayMorning ARIA attributes", () => {
  it("renders the hero heading as h1", () => {
    render(<MondayMorning plan={basePlan} profile={baseProfile} />);
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toBeInTheDocument();
    expect(heading.textContent).toMatch(/what you can do/i);
  });

  it("renders section element as landmark", () => {
    const { container } = render(<MondayMorning plan={basePlan} profile={baseProfile} />);
    expect(container.querySelector("section")).toBeInTheDocument();
  });
});
