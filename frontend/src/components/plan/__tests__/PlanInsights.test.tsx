import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { PlanInsights } from "../PlanInsights";

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({
    data: {
      steps: [
        {
          order: 1,
          barrier_id: "credit",
          barrier_name: "Credit",
          category: "financial",
          playbook: "Check your credit report",
          unlocks: [],
        },
      ],
      total_barriers: 1,
      has_cycles: false,
    },
    isLoading: false,
  })),
}));

vi.mock("@/lib/api", () => ({
  getBarrierSequence: vi.fn(),
  simulateBarriers: vi.fn().mockResolvedValue({
    barriers_resolved: ["credit"],
    barriers_remaining: [],
    unlocked_barriers: [],
    jobs_unlocked_estimate: 8,
    benefits_unlocked: [],
    sequence_after: { steps: [], total_barriers: 0, has_cycles: false },
  }),
}));

describe("PlanInsights", () => {
  it("renders barrier sequence viz when barriers present", () => {
    render(
      <PlanInsights
        sessionId="00000000-0000-4000-8000-000000000001"
        token="test-token"
        barriers={["credit"]}
      />,
    );
    // Both BarrierSequenceViz and WhatHappensIf show "Credit"
    expect(screen.getAllByText(/Credit/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Barrier Resolution Order/i)).toBeInTheDocument();
  });

  it("renders WhatHappensIf component", () => {
    render(
      <PlanInsights
        sessionId="00000000-0000-4000-8000-000000000001"
        token="test-token"
        barriers={["credit"]}
      />,
    );
    expect(screen.getByText(/What Happens If/i)).toBeInTheDocument();
  });

  it("returns null when no barriers", () => {
    const { container } = render(
      <PlanInsights
        sessionId="00000000-0000-4000-8000-000000000001"
        token="test-token"
        barriers={[]}
      />,
    );
    expect(container.innerHTML).toBe("");
  });
});
