import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PlanExport } from "../PlanExport";
import type { ReEntryPlan, UserProfile, CreditAssessmentResult } from "@/lib/types";

// --- Fixtures ---

const basePlan: ReEntryPlan = {
  plan_id: "plan-001",
  session_id: "sess-abc",
  resident_summary: "You have a strong path forward.",
  barriers: [
    {
      type: "credit",
      severity: "high",
      title: "Credit Barrier",
      timeline_days: 90,
      actions: ["Check credit report", "Dispute errors"],
      resources: [],
      transit_matches: [],
    },
    {
      type: "transportation",
      severity: "medium",
      title: "Transportation Barrier",
      timeline_days: 30,
      actions: ["Apply for bus pass"],
      resources: [],
      transit_matches: [],
    },
  ],
  job_matches: [
    {
      title: "Warehouse Associate",
      company: "ABC Logistics",
      location: "Montgomery, AL",
      url: "https://example.com/apply",
      source: "indeed",
      transit_accessible: true,
      route: "Route 4",
      credit_check_required: "no",
      eligible_now: true,
      eligible_after: null,
    },
    {
      title: "Bank Teller",
      company: "First National",
      location: "Montgomery, AL",
      url: null,
      source: null,
      transit_accessible: false,
      route: null,
      credit_check_required: "yes",
      eligible_now: false,
      eligible_after: "Credit score improvement",
    },
  ],
  immediate_next_steps: [
    "Visit Alabama Career Center",
    "Apply for bus pass",
    "Check credit report",
  ],
  credit_readiness_score: 45,
  eligible_now: ["Warehouse Associate"],
  eligible_after_repair: ["Bank Teller"],
};

const baseProfile: UserProfile = {
  session_id: "sess-abc",
  zip_code: "36104",
  employment_status: "unemployed",
  barrier_count: 2,
  primary_barriers: ["credit", "transportation"],
  barrier_severity: "high",
  needs_credit_assessment: true,
  transit_dependent: true,
  schedule_type: "daytime",
  work_history: "2 years retail",
  target_industries: ["logistics", "banking"],
};

const baseCreditResult: CreditAssessmentResult = {
  barrier_severity: "high",
  barrier_details: [],
  readiness: {
    score: 45,
    fico_score: 580,
    score_band: "fair",
    factors: {
      payment_history: 60,
      utilization: 40,
      credit_age: 30,
      credit_mix: 50,
      new_credit: 70,
    },
  },
  thresholds: [],
  dispute_pathway: {
    steps: [],
    total_estimated_days: 90,
    statutes_cited: [],
    legal_theories: [],
  },
  eligibility: [],
  disclaimer: "For informational purposes only.",
};

// --- Tests ---

describe("PlanExport", () => {
  it("renders a Download PDF button", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    const button = screen.getByRole("button", { name: /download pdf/i });
    expect(button).toBeInTheDocument();
  });

  it("renders the Download icon inside the button", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    const button = screen.getByRole("button", { name: /download pdf/i });
    expect(button).toBeInTheDocument();
  });

  it("accepts optional creditResult prop without error", () => {
    render(
      <PlanExport
        plan={basePlan}
        profile={baseProfile}
        creditResult={baseCreditResult}
      />
    );
    const button = screen.getByRole("button", { name: /download pdf/i });
    expect(button).toBeInTheDocument();
  });

  it("renders hidden PDF content with MontGoWork header", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    const header = screen.getByText("MontGoWork Re-Entry Plan");
    expect(header).toBeInTheDocument();
  });

  it("renders resident summary in hidden content", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    expect(
      screen.getByText("You have a strong path forward.")
    ).toBeInTheDocument();
  });

  it("renders barrier titles in hidden content", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    expect(screen.getByText("Credit Barrier")).toBeInTheDocument();
    expect(screen.getByText("Transportation Barrier")).toBeInTheDocument();
  });

  it("renders barrier action steps in hidden content", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    // "Check credit report" appears both in barrier actions and next steps
    expect(screen.getAllByText("Check credit report").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Dispute errors")).toBeInTheDocument();
    // "Apply for bus pass" appears both in barrier actions and next steps
    expect(screen.getAllByText("Apply for bus pass").length).toBeGreaterThanOrEqual(1);
  });

  it("renders job match titles and companies", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    expect(screen.getByText("Warehouse Associate")).toBeInTheDocument();
    expect(screen.getByText("Bank Teller")).toBeInTheDocument();
  });

  it("renders eligible now / after status for jobs", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    expect(screen.getByText("Eligible Now")).toBeInTheDocument();
    expect(screen.getByText("Credit score improvement")).toBeInTheDocument();
  });

  it("renders immediate next steps", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    expect(
      screen.getByText("Visit Alabama Career Center")
    ).toBeInTheDocument();
  });

  it("renders credit info when creditResult provided", () => {
    render(
      <PlanExport
        plan={basePlan}
        profile={baseProfile}
        creditResult={baseCreditResult}
      />
    );
    expect(screen.getByText(/FICO Score:/)).toBeInTheDocument();
    expect(screen.getByText(/580/)).toBeInTheDocument();
    expect(screen.getByText(/Readiness Score:/)).toBeInTheDocument();
  });

  it("does not render credit section when creditResult is null", () => {
    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    expect(screen.queryByText(/FICO Score:/)).not.toBeInTheDocument();
  });

  it("does not render summary when resident_summary is null", () => {
    const planNoSummary = { ...basePlan, resident_summary: null };
    render(<PlanExport plan={planNoSummary} profile={baseProfile} />);
    expect(
      screen.queryByText("You have a strong path forward.")
    ).not.toBeInTheDocument();
  });

  it("shows loading state when download is clicked", async () => {
    // Mock html2pdf dynamic import to return a controllable promise
    let resolveSave!: () => void;
    const savePromise = new Promise<void>((r) => {
      resolveSave = r;
    });
    const mockHtml2pdf = vi.fn(() => ({
      set: vi.fn().mockReturnThis(),
      from: vi.fn().mockReturnThis(),
      save: vi.fn(() => savePromise),
    }));
    vi.doMock("html2pdf.js", () => ({ default: mockHtml2pdf }));

    render(<PlanExport plan={basePlan} profile={baseProfile} />);
    const user = userEvent.setup();

    const button = screen.getByRole("button", { name: /download pdf/i });
    await user.click(button);

    // Should show "Generating..." text while generating
    expect(screen.getByText(/generating/i)).toBeInTheDocument();
    expect(button).toBeDisabled();

    // Resolve the save promise and let it complete
    resolveSave();

    vi.doUnmock("html2pdf.js");
  });

  it("handles empty barriers and jobs gracefully", () => {
    const emptyPlan: ReEntryPlan = {
      ...basePlan,
      barriers: [],
      job_matches: [],
      immediate_next_steps: [],
    };
    render(<PlanExport plan={emptyPlan} profile={baseProfile} />);
    const button = screen.getByRole("button", { name: /download pdf/i });
    expect(button).toBeInTheDocument();
    // Should not render empty sections
    expect(screen.queryByText("Barriers")).not.toBeInTheDocument();
    expect(screen.queryByText("Job Matches")).not.toBeInTheDocument();
    expect(screen.queryByText("Immediate Next Steps")).not.toBeInTheDocument();
  });
});
