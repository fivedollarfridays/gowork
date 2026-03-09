import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

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
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockUseReducedMotion.mockReturnValue(false);
    mockSearchParams.set("session", "sess-anim-test");
    mockSearchParams.set("token", "test-token-anim");
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows transition screen with motivational message while loading", async () => {
    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}));

    renderWithClient(<PlanPage />);
    // Transition screen shows motivational text and loading indicator
    expect(screen.getByText(/analyzing your profile/i)).toBeInTheDocument();
  });

  it("fires confetti after transition completes with data", async () => {
    mockUseReducedMotion.mockReturnValue(false);
    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockResolvedValue(fakePlanResponse);

    renderWithClient(<PlanPage />);

    // Advance through transition phases (2.5s + 2.5s + 0.6s)
    await vi.advanceTimersByTimeAsync(6000);

    await waitFor(() => {
      expect(mockConfetti).toHaveBeenCalledTimes(1);
    }, { timeout: 2000 });
    expect(mockConfetti).toHaveBeenCalledWith(
      expect.objectContaining({ particleCount: 80, spread: 70 }),
    );
  });

  it("does NOT fire confetti when reduced motion is preferred", async () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockResolvedValue(fakePlanResponse);

    renderWithClient(<PlanPage />);

    // With reduced motion, transition completes immediately when data ready
    await waitFor(() => {
      expect(screen.getByText(/here.?s what you can do/i)).toBeInTheDocument();
    }, { timeout: 2000 });

    // Give time for any potential confetti call
    await vi.advanceTimersByTimeAsync(500);
    expect(mockConfetti).not.toHaveBeenCalled();
  });
});
