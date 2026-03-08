import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PlanPage from "../plan/page";

const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/lib/api", () => ({
  getPlan: vi.fn(),
  generateNarrative: vi.fn(),
  getJobs: vi.fn().mockResolvedValue({ jobs: [], total: 0 }),
}));

const MOCK_PLAN_RESPONSE = {
  session_id: "sess-credit-test",
  barriers: ["credit"],
  qualifications: "Some work",
  plan: {
    plan_id: "p1",
    session_id: "sess-credit-test",
    resident_summary: null,
    barriers: [],
    job_matches: [],
    strong_matches: [],
    possible_matches: [],
    after_repair: [],
    immediate_next_steps: ["Visit career center"],
    credit_readiness_score: null,
    eligible_now: [],
    eligible_after_repair: [],
    wioa_eligibility: null,
  },
  credit_profile: null,
};

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("PlanPage credit data fallback", () => {
  beforeEach(() => {
    mockSearchParams.delete("session");
    mockSearchParams.delete("token");
    sessionStorage.clear();
  });

  it("falls back to backend credit_profile when sessionStorage is empty", async () => {
    mockSearchParams.set("session", "sess-credit-test");
    mockSearchParams.set("token", "test-token");

    const backendCredit = {
      barrier_severity: "high",
      barrier_details: [],
      readiness: { score: 45, fico_score: 580, score_band: "fair", factors: {} },
      thresholds: [],
      dispute_pathway: { steps: [], total_estimated_days: 0, statutes_cited: [], legal_theories: [] },
      eligibility: [],
      disclaimer: "Info only.",
    };

    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ...MOCK_PLAN_RESPONSE,
      credit_profile: backendCredit,
    });

    renderWithClient(<PlanPage />);

    await waitFor(() => {
      expect(screen.getAllByText(/credit assessment/i).length).toBeGreaterThan(0);
    });
  });

  it("uses sessionStorage credit data when available (faster)", async () => {
    mockSearchParams.set("session", "sess-credit-test");
    mockSearchParams.set("token", "test-token");

    const localCredit = {
      barrier_severity: "medium",
      barrier_details: [],
      readiness: { score: 65, fico_score: 680, score_band: "good", factors: {} },
      thresholds: [],
      dispute_pathway: { steps: [], total_estimated_days: 0, statutes_cited: [], legal_theories: [] },
      eligibility: [],
      disclaimer: "Info only.",
    };
    sessionStorage.setItem("credit_sess-credit-test", JSON.stringify(localCredit));

    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ...MOCK_PLAN_RESPONSE,
      credit_profile: null,
    });

    renderWithClient(<PlanPage />);

    await waitFor(() => {
      expect(screen.getAllByText(/credit assessment/i).length).toBeGreaterThan(0);
    });
  });
});
