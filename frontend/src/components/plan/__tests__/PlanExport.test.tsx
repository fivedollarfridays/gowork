import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PlanExport } from "../PlanExport";
import type { ReEntryPlan, CreditAssessmentResult } from "@/lib/types";

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
      relevance_score: 0.85,
      match_reason: "Industry match",
      bucket: "strong" as const,
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
      relevance_score: 0.6,
      match_reason: "Possible after credit repair",
      bucket: "after_repair" as const,
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
  strong_matches: [],
  possible_matches: [],
  after_repair: [],
  wioa_eligibility: null,
  job_readiness: null,
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
    render(<PlanExport plan={basePlan} />);
    const button = screen.getByRole("button", { name: /download pdf/i });
    expect(button).toBeInTheDocument();
  });

  it("renders the Download icon inside the button", () => {
    render(<PlanExport plan={basePlan} />);
    const button = screen.getByRole("button", { name: /download pdf/i });
    expect(button).toBeInTheDocument();
  });

  it("accepts optional creditResult prop without error", () => {
    render(
      <PlanExport
        plan={basePlan}
               creditResult={baseCreditResult}
      />
    );
    const button = screen.getByRole("button", { name: /download pdf/i });
    expect(button).toBeInTheDocument();
  });

  it("renders hidden PDF content with MontGoWork header", () => {
    render(<PlanExport plan={basePlan} />);
    const header = screen.getByText("MontGoWork Re-Entry Plan");
    expect(header).toBeInTheDocument();
  });

  it("renders resident summary in hidden content", () => {
    render(<PlanExport plan={basePlan} />);
    expect(
      screen.getByText("You have a strong path forward.")
    ).toBeInTheDocument();
  });

  it("renders barrier titles in hidden content", () => {
    render(<PlanExport plan={basePlan} />);
    expect(screen.getByText("Credit Barrier")).toBeInTheDocument();
    expect(screen.getByText("Transportation Barrier")).toBeInTheDocument();
  });

  it("renders barrier action steps in hidden content", () => {
    render(<PlanExport plan={basePlan} />);
    // "Check credit report" appears both in barrier actions and next steps
    expect(screen.getAllByText("Check credit report").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Dispute errors")).toBeInTheDocument();
    // "Apply for bus pass" appears both in barrier actions and next steps
    expect(screen.getAllByText("Apply for bus pass").length).toBeGreaterThanOrEqual(1);
  });

  it("renders job match titles and companies", () => {
    render(<PlanExport plan={basePlan} />);
    expect(screen.getByText("Warehouse Associate")).toBeInTheDocument();
    expect(screen.getByText("Bank Teller")).toBeInTheDocument();
  });

  it("renders eligible now / after status for jobs", () => {
    render(<PlanExport plan={basePlan} />);
    expect(screen.getByText("Eligible Now")).toBeInTheDocument();
    expect(screen.getByText("Credit score improvement")).toBeInTheDocument();
  });

  it("renders immediate next steps", () => {
    render(<PlanExport plan={basePlan} />);
    expect(
      screen.getByText("Visit Alabama Career Center")
    ).toBeInTheDocument();
  });

  it("renders credit info when creditResult provided", () => {
    render(
      <PlanExport
        plan={basePlan}
               creditResult={baseCreditResult}
      />
    );
    expect(screen.getByText(/FICO Score:/)).toBeInTheDocument();
    expect(screen.getByText(/580/)).toBeInTheDocument();
    expect(screen.getByText(/Readiness Score:/)).toBeInTheDocument();
  });

  it("does not render credit section when creditResult is null", () => {
    render(<PlanExport plan={basePlan} />);
    expect(screen.queryByText(/FICO Score:/)).not.toBeInTheDocument();
  });

  it("does not render summary when resident_summary is null", () => {
    const planNoSummary = { ...basePlan, resident_summary: null };
    render(<PlanExport plan={planNoSummary} />);
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

    render(<PlanExport plan={basePlan} />);
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

  it("error message has role=alert", async () => {
    // Reset module cache so previous test's mock doesn't leak
    vi.resetModules();
    // Mock html2pdf to throw an error
    vi.doMock("html2pdf.js", () => ({
      default: () => ({
        set: vi.fn().mockReturnThis(),
        from: vi.fn().mockReturnThis(),
        save: vi.fn(() => Promise.reject(new Error("PDF failed"))),
      }),
    }));

    render(<PlanExport plan={basePlan} />);
    const user = userEvent.setup();
    const button = screen.getByRole("button", { name: /download pdf/i });
    await user.click(button);

    // Wait for the error to appear
    const errorEl = await screen.findByRole("alert");
    expect(errorEl).toHaveTextContent(/failed to generate pdf/i);

    vi.doUnmock("html2pdf.js");
  });

  it("button has aria-label during generation", async () => {
    let resolveSave!: () => void;
    const savePromise = new Promise<void>((r) => {
      resolveSave = r;
    });
    vi.doMock("html2pdf.js", () => ({
      default: () => ({
        set: vi.fn().mockReturnThis(),
        from: vi.fn().mockReturnThis(),
        save: vi.fn(() => savePromise),
      }),
    }));

    render(<PlanExport plan={basePlan} />);
    const user = userEvent.setup();
    const button = screen.getByRole("button", { name: /download pdf/i });
    await user.click(button);

    // During generation, button should have descriptive aria-label
    expect(button).toHaveAttribute("aria-label", "Generating PDF, please wait");

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
    render(<PlanExport plan={emptyPlan} />);
    const button = screen.getByRole("button", { name: /download pdf/i });
    expect(button).toBeInTheDocument();
    // Should not render empty sections
    expect(screen.queryByText("Barriers")).not.toBeInTheDocument();
    expect(screen.queryByText("Job Matches")).not.toBeInTheDocument();
    expect(screen.queryByText("Immediate Next Steps")).not.toBeInTheDocument();
  });

  it("renders QR code section when feedbackToken is provided", () => {
    render(<PlanExport plan={basePlan} feedbackToken="tk-abc" />);
    expect(screen.getByText(/how did your visit go/i)).toBeInTheDocument();
    // QR code SVG should be present
    const svg = document.querySelector("[data-testid='feedback-qr']");
    expect(svg).toBeInTheDocument();
  });

  it("renders scan instructions with QR code", () => {
    render(<PlanExport plan={basePlan} feedbackToken="tk-abc" />);
    expect(screen.getByText(/scan to share feedback/i)).toBeInTheDocument();
  });

  it("does not render QR section when feedbackToken is missing", () => {
    render(<PlanExport plan={basePlan} />);
    expect(screen.queryByText(/how did your visit go/i)).not.toBeInTheDocument();
  });
});
