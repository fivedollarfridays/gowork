import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { OutcomesBadge } from "../OutcomesBadge";
import { useQuery } from "@tanstack/react-query";

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({
    data: { assessment_count: 87, top_barriers: [{ barrier: "credit", count: 45 }] },
    isLoading: false,
  })),
}));

describe("OutcomesBadge", () => {
  beforeEach(() => {
    (useQuery as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { assessment_count: 87, top_barriers: [{ barrier: "credit", count: 45 }] },
      isLoading: false,
    });
  });

  it("renders assessment count", () => {
    render(<OutcomesBadge />);
    expect(screen.getByText(/87/)).toBeInTheDocument();
  });

  it("renders descriptive text", () => {
    render(<OutcomesBadge />);
    expect(screen.getByText(/assessments completed/i)).toBeInTheDocument();
  });

  it("renders nothing when loading", () => {
    (useQuery as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: true,
    });
    const { container } = render(<OutcomesBadge />);
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing when count is zero", () => {
    (useQuery as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { assessment_count: 0, top_barriers: [] },
      isLoading: false,
    });
    const { container } = render(<OutcomesBadge />);
    expect(container.innerHTML).toBe("");
  });

  it("shows improvement messaging when top barriers present", () => {
    render(<OutcomesBadge />);
    expect(screen.getByText(/improving recommendations/i)).toBeInTheDocument();
  });
});
