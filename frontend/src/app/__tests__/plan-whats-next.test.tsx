import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
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

vi.mock("canvas-confetti", () => ({ default: vi.fn() }));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("PlanPage What's Next CTA", () => {
  beforeEach(async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockSearchParams.set("session", "sess-cta-test");
    mockSearchParams.set("token", "test-token-cta");
    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockResolvedValue({
      session_id: "sess-cta-test",
      barriers: ["credit"],
      qualifications: null,
      plan: {
        plan_id: "plan-1",
        session_id: "sess-cta-test",
        resident_summary: null,
        barriers: [],
        job_matches: [],
        strong_matches: [],
        possible_matches: [],
        after_repair: [],
        immediate_next_steps: ["Visit the career center"],
        credit_readiness_score: null,
        eligible_now: [],
        eligible_after_repair: [],
        wioa_eligibility: null,
      },
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders What's Next section with career center info", async () => {
    renderWithClient(<PlanPage />);

    // Advance through transition screen
    await vi.advanceTimersByTimeAsync(6000);

    await waitFor(() => {
      expect(screen.getByText(/what.?s next/i)).toBeInTheDocument();
    });

    expect(screen.getAllByText(/1060 East South Boulevard/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/334-286-1746/i).length).toBeGreaterThanOrEqual(1);
  });

  it("renders Start New Assessment link", async () => {
    renderWithClient(<PlanPage />);

    // Advance through transition screen
    await vi.advanceTimersByTimeAsync(6000);

    await waitFor(() => {
      expect(screen.getByText(/what.?s next/i)).toBeInTheDocument();
    });

    const link = screen.getByRole("link", { name: /start new assessment/i });
    expect(link).toHaveAttribute("href", "/assess");
  });
});
