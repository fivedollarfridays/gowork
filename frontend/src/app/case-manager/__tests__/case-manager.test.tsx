import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import CaseManagerPage from "../page";

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({
    data: {
      total_assessments: 42,
      common_barriers: [
        { barrier: "credit", count: 30 },
        { barrier: "transportation", count: 25 },
      ],
      total_barrier_instances: 120,
    },
    isLoading: false,
    error: null,
  })),
}));

describe("CaseManagerPage", () => {
  it("renders the dashboard heading", () => {
    render(<CaseManagerPage />);
    expect(screen.getByText(/Case Manager Dashboard/i)).toBeInTheDocument();
  });

  it("shows total assessments", () => {
    render(<CaseManagerPage />);
    expect(screen.getByText(/42/)).toBeInTheDocument();
  });

  it("shows common barriers", () => {
    render(<CaseManagerPage />);
    expect(screen.getByText(/credit/i)).toBeInTheDocument();
    expect(screen.getByText(/transportation/i)).toBeInTheDocument();
  });
});
