import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock framer-motion
const mockUseReducedMotion = vi.fn(() => false);
vi.mock("framer-motion", async () => {
  const actual = await vi.importActual("framer-motion");
  return { ...actual, useReducedMotion: () => mockUseReducedMotion() };
});

// Mock canvas-confetti
const mockConfetti = vi.fn();
vi.mock("canvas-confetti", () => ({
  default: (...args: unknown[]) => mockConfetti(...args),
}));

// Mock next/navigation
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

// Mock API
vi.mock("@/lib/api", () => ({
  getPlan: vi.fn(),
  generateNarrative: vi.fn(),
  getJobs: vi.fn().mockResolvedValue({ jobs: [], total: 0 }),
}));

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PlanPage from "../plan/page";

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

const fakePlanResponse = {
  session_id: "sess-anim-test",
  barriers: ["credit"],
  qualifications: null,
  plan: {
    plan_id: "plan-anim",
    session_id: "sess-anim-test",
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
};

describe("PlanPage animations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseReducedMotion.mockReturnValue(false);
    mockSearchParams.set("session", "sess-anim-test");
    mockSearchParams.set("token", "test-token-anim");
  });

  it("renders ShimmerBar during loading state", async () => {
    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}));

    const { container } = renderWithClient(<PlanPage />);
    const shimmerBars = container.querySelectorAll("[class*='bg-muted']");
    expect(shimmerBars.length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/loading your plan/i)).toBeInTheDocument();
  });

  it("fires confetti once when data loads", async () => {
    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockResolvedValue(fakePlanResponse);

    renderWithClient(<PlanPage />);
    await screen.findByText(/here.?s what you can do/i);

    await waitFor(() => {
      expect(mockConfetti).toHaveBeenCalledTimes(1);
    });
    expect(mockConfetti).toHaveBeenCalledWith(
      expect.objectContaining({ particleCount: 60 }),
    );
  });

  it("does NOT fire confetti when reduced motion is preferred", async () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockResolvedValue(fakePlanResponse);

    renderWithClient(<PlanPage />);
    await screen.findByText(/here.?s what you can do/i);

    // Give time for any potential confetti call
    await new Promise((r) => setTimeout(r, 50));
    expect(mockConfetti).not.toHaveBeenCalled();
  });
});
