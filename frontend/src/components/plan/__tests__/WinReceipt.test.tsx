/**
 * WinReceipt — the plan-completion dopamine moment.
 *
 * The page already had: PlanTransition (loading), MondayMorning (next steps),
 * ActionTimeline, and a tiny outline "Download PDF" button buried at the
 * bottom in a "What's Next" card.  WinReceipt sits ABOVE MondayMorning,
 * fires once on first paint, and rewards the user for finishing — the
 * personalized headline, the wage ticker (top match × 2080hrs), the live
 * stat triplet (jobs/fair-chance/transit-accessible), and the gradient
 * RECEIPT card whose primary CTA is the PDF download.
 *
 * Doesn't replace PlanExport — both coexist (legacy users who scroll back
 * still find the outline button).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { WinReceipt } from "../WinReceipt";
import type { ReEntryPlan, ScoredJobMatch } from "@/lib/types";

// Pin framer's reduced-motion hook to ON in jsdom so the AnimatedCounter
// renders its static final-state branch.  We're testing the *math* and
// the *DOM contract* of WinReceipt, not framer's spring loop (which has
// no paint loop in jsdom and would make every test depend on a wallclock
// timeout).  The component's reduced-motion branch is a non-trivial part
// of the spec anyway — accessibility tests would require it.
vi.mock("framer-motion", async () => {
  const actual = await vi.importActual<typeof import("framer-motion")>("framer-motion");
  return { ...actual, useReducedMotion: () => true };
});

function _job(overrides: Partial<ScoredJobMatch> = {}): ScoredJobMatch {
  return {
    title: "Wastewater Operator Trainee",
    company: "Trinity River Authority",
    location: "Arlington, TX 76011",
    pay_range: "$20.50/hr",
    relevance_score: 0.8,
    match_reason: "Forklift cert match",
    transit_accessible: false,
    fair_chance: true,
    eligible_now: true,
    eligible_after: null,
    bucket: "strong",
    cliff_impact: null,
    score_breakdown: null,
    transit_info: null,
    commute_estimate: null,
    distance_miles: null,
    data_source: null,
    ...overrides,
  } as ScoredJobMatch;
}

function _plan(overrides: Partial<ReEntryPlan> = {}): ReEntryPlan {
  const matches: ScoredJobMatch[] = [
    _job({ title: "Wastewater Operator Trainee", pay_range: "$20.50/hr", fair_chance: true, transit_accessible: false }),
    _job({ title: "Warehouse Associate", pay_range: "$14.00/hr", fair_chance: true, transit_accessible: true }),
    _job({ title: "Pest Control Technician", pay_range: "$20.00/hr", fair_chance: true, transit_accessible: true }),
  ];
  return {
    plan_id: "plan-1",
    session_id: "00000000-0000-4000-8000-000000000001",
    resident_summary: null,
    barriers: [],
    job_matches: matches,
    strong_matches: matches,
    possible_matches: [],
    after_repair: [],
    immediate_next_steps: [],
    credit_readiness_score: null,
    eligible_now: matches,
    eligible_after_repair: [],
    wioa_eligibility: null,
    job_readiness: null,
    ...overrides,
  } as ReEntryPlan;
}

beforeEach(() => {
  // Pin matchMedia so framer-motion's useReducedMotion hook resolves
  // deterministically in jsdom.  Each test that needs reduced motion
  // overrides this.
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
  // Mock fetch so the receipt's PDF download tests don't hit network.
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    blob: () => Promise.resolve(new Blob(["%PDF-1.4 stub"], { type: "application/pdf" })),
  }) as unknown as typeof fetch;
  sessionStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});


describe("WinReceipt headline", () => {
  it("uses persona name when provided", () => {
    render(<WinReceipt plan={_plan()} sessionId="sess-1" token="tok-1" personaName="Carlos" />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/Carlos.*plan/i);
  });

  it("falls back to a generic greeting when no name is present", () => {
    render(<WinReceipt plan={_plan()} sessionId="sess-1" token="tok-1" />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/your plan/i);
  });
});


describe("WinReceipt wage ticker", () => {
  it("annualizes the top job's hourly pay (rate × 2080)", async () => {
    // useReducedMotion is mocked to true at module scope — the static
    // branch of AnimatedCounter renders the final number on first paint.
    render(<WinReceipt plan={_plan()} sessionId="sess-1" token="tok-1" />);
    // $20.50 × 2080 = $42,640.
    const node = screen.getByTestId("win-receipt-wage");
    expect(node.textContent ?? "").toMatch(/\$42,640/);
  });

  it("hides the wage ticker when no matches have a pay_range", () => {
    const plan = _plan({
      job_matches: [_job({ pay_range: null })],
      strong_matches: [_job({ pay_range: null })],
    });
    render(<WinReceipt plan={plan} sessionId="sess-1" token="tok-1" />);
    expect(screen.queryByTestId("win-receipt-wage")).toBeNull();
  });
});


describe("WinReceipt stat triplet", () => {
  it("shows job count, fair-chance count, and transit-accessible percent", () => {
    render(<WinReceipt plan={_plan()} sessionId="sess-1" token="tok-1" />);
    const stats = screen.getByTestId("win-receipt-stats");
    expect(stats.textContent ?? "").toMatch(/3.*matched/i);
    // 3/3 fair_chance
    expect(stats.textContent ?? "").toMatch(/3.*fair[- ]chance/i);
    // 2/3 transit-accessible -> 67%
    expect(stats.textContent ?? "").toMatch(/67%/);
  });
});


describe("WinReceipt PDF download", () => {
  it("calls /api/plan/{sessionId}/pdf with the token when clicked", async () => {
    const fetchSpy = global.fetch as ReturnType<typeof vi.fn>;
    render(<WinReceipt plan={_plan()} sessionId="sess-abc" token="tok-xyz" />);
    fireEvent.click(screen.getByRole("button", { name: /take it with you/i }));
    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    const calledUrl = fetchSpy.mock.calls[0]?.[0] as string;
    expect(calledUrl).toContain("/api/plan/sess-abc/pdf");
    expect(calledUrl).toContain("token=tok-xyz");
  });

  it("renders an error message when the PDF fetch fails", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 }) as unknown as typeof fetch;
    render(<WinReceipt plan={_plan()} sessionId="sess-1" token="tok-1" />);
    fireEvent.click(screen.getByRole("button", { name: /take it with you/i }));
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/couldn't.*download/i),
    );
  });

  it("flashes a 'Saved.' affirmation after a successful download", async () => {
    render(<WinReceipt plan={_plan()} sessionId="sess-1" token="tok-1" />);
    fireEvent.click(screen.getByRole("button", { name: /take it with you/i }));
    await waitFor(() =>
      expect(screen.getByTestId("win-receipt-saved-flash")).toHaveTextContent(/saved/i),
    );
  });
});


describe("WinReceipt accessibility", () => {
  it("renders a single h1 (page-level landmark)", () => {
    render(<WinReceipt plan={_plan()} sessionId="sess-1" token="tok-1" />);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  it("download button has an accessible label", () => {
    render(<WinReceipt plan={_plan()} sessionId="sess-1" token="tok-1" />);
    const btn = screen.getByRole("button", { name: /take it with you/i });
    expect(btn).toHaveAttribute("aria-label");
  });
});
