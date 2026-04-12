import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { OutcomesBadge } from "../OutcomesBadge";

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({
    data: { assessment_count: 87, top_barriers: [{ barrier: "credit", count: 45 }] },
    isLoading: false,
  })),
}));

describe("OutcomesBadge", () => {
  it("renders assessment count", () => {
    render(<OutcomesBadge />);
    expect(screen.getByText(/87/)).toBeInTheDocument();
  });

  it("renders descriptive text", () => {
    render(<OutcomesBadge />);
    expect(screen.getByText(/assessments completed/i)).toBeInTheDocument();
  });
});
