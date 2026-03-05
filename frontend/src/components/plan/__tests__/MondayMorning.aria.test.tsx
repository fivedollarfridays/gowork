import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MondayMorning } from "../MondayMorning";
import type { ReEntryPlan, UserProfile } from "@/lib/types";
import { AvailableHours, BarrierType, EmploymentStatus } from "@/lib/types";

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
};

describe("MondayMorning ARIA attributes", () => {
  it("narrative loading card is wrapped in aria-live=polite", () => {
    render(
      <MondayMorning
        plan={basePlan}
        profile={baseProfile}
        narrative={null}
        narrativeLoading={true}
      />
    );

    const loadingText = screen.getByText(/generating your personalized summary/i);
    // The loading text should be inside an aria-live region
    const liveRegion = loadingText.closest("[aria-live]");
    expect(liveRegion).toHaveAttribute("aria-live", "polite");
  });

  it("does not render aria-live region when not loading", () => {
    render(
      <MondayMorning
        plan={basePlan}
        profile={baseProfile}
        narrative={null}
        narrativeLoading={false}
      />
    );

    expect(screen.queryByText(/generating your personalized summary/i)).not.toBeInTheDocument();
  });
});
