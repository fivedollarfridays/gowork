/**
 * Empty-profile handling for the "What Changes in 3 Months" comparison
 * (S13-T72 fix). With no barriers + no jobs the component used to render
 * degenerate "0 active → No barriers identified" and "0 eligible now → 0
 * eligible after plan completion" rows. The fix hides those rows and the
 * whole section when there's nothing meaningful to compare.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ComparisonView } from "../ComparisonView";
import {
  AvailableHours,
  BarrierSeverity,
  BarrierType,
  EmploymentStatus,
  type ReEntryPlan,
  type UserProfile,
} from "@/lib/types";

const emptyPlan: ReEntryPlan = {
  plan_id: "plan-empty",
  session_id: "sess-empty",
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

const emptyProfile: UserProfile = {
  session_id: "sess-empty",
  zip_code: "",
  employment_status: EmploymentStatus.UNEMPLOYED,
  barrier_count: 0,
  primary_barriers: [],
  barrier_severity: BarrierSeverity.LOW,
  needs_credit_assessment: false,
  transit_dependent: false,
  schedule_type: AvailableHours.DAYTIME,
  work_history: "",
  target_industries: [],
  record_profile: null,
};

describe("ComparisonView — empty profile", () => {
  it("does not render degenerate '0 active' / 'No barriers identified' rows", () => {
    render(<ComparisonView plan={emptyPlan} profile={emptyProfile} />);
    // The misleading copy from the bug report must not appear.
    expect(screen.queryByText(/0 active/i)).toBeNull();
    expect(screen.queryByText(/No barriers identified/i)).toBeNull();
  });

  it("does not render degenerate '0 eligible now' / '0 eligible after' rows", () => {
    render(<ComparisonView plan={emptyPlan} profile={emptyProfile} />);
    expect(screen.queryByText(/0 eligible now/i)).toBeNull();
    expect(screen.queryByText(/0 eligible after plan completion/i)).toBeNull();
  });

  it("hides the entire 'What Changes in 3 Months' section when there's nothing to compare", () => {
    const { container } = render(
      <ComparisonView plan={emptyPlan} profile={emptyProfile} />,
    );
    expect(screen.queryByText(/What Changes in 3 Months/i)).toBeNull();
    // No section element rendered at all.
    expect(container.querySelector("section")).toBeNull();
  });
});

describe("ComparisonView — populated profile", () => {
  it("renders barrier and job rows when data is present", () => {
    const populatedPlan: ReEntryPlan = {
      ...emptyPlan,
      barriers: [
        {
          type: BarrierType.TRANSPORTATION,
          severity: BarrierSeverity.MEDIUM,
          title: "Transportation",
          timeline_days: 30,
          actions: ["Apply for transit pass"],
          resources: [],
          transit_matches: [],
        },
      ],
      strong_matches: [
        {
          title: "Cashier",
          company: "Walmart",
          location: "Montgomery",
          url: null,
          source: "test",
          transit_accessible: true,
          route: null,
          credit_check_required: "no",
          eligible_now: true,
          eligible_after: null,
          relevance_score: 0.8,
          match_reason: "skills match",
          bucket: "strong",
        },
      ],
    };
    const populatedProfile: UserProfile = {
      ...emptyProfile,
      barrier_count: 1,
      primary_barriers: [BarrierType.TRANSPORTATION],
      barrier_severity: BarrierSeverity.MEDIUM,
      transit_dependent: true,
    };

    render(<ComparisonView plan={populatedPlan} profile={populatedProfile} />);

    expect(screen.getByText(/What Changes in 3 Months/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Barriers/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Job Matches/i).length).toBeGreaterThan(0);
  });

  it("still renders Job Matches row when only the after-plan eligible count is positive", () => {
    const planWithFutureJobs: ReEntryPlan = {
      ...emptyPlan,
      after_repair: [
        {
          title: "Forklift Operator",
          company: "Amazon",
          location: "Montgomery",
          url: null,
          source: "test",
          transit_accessible: true,
          route: null,
          credit_check_required: "yes",
          eligible_now: false,
          eligible_after: "after credit repair",
          relevance_score: 0.6,
          match_reason: "credit gate",
          bucket: "after_repair",
        },
      ],
      eligible_after_repair: ["Forklift Operator"],
    };
    render(<ComparisonView plan={planWithFutureJobs} profile={emptyProfile} />);
    expect(screen.getByText(/What Changes in 3 Months/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Job Matches/i).length).toBeGreaterThan(0);
  });
});
