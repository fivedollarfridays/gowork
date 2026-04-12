import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import CaseManagerPage from "../page";
import { useQuery } from "@tanstack/react-query";

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
  beforeEach(() => {
    (useQuery as ReturnType<typeof vi.fn>).mockReturnValue({
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
    });
  });

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

  it("shows loading state", () => {
    (useQuery as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
    render(<CaseManagerPage />);
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    (useQuery as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Server down"),
    });
    render(<CaseManagerPage />);
    expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
  });

  it("computes average barriers per person", () => {
    render(<CaseManagerPage />);
    // 120 / 42 = 2.857... rounded to 2.9
    expect(screen.getByText("2.9")).toBeInTheDocument();
  });

  it("shows barrier percentage in bar chart", () => {
    render(<CaseManagerPage />);
    // credit: 30/42 = 71%
    expect(screen.getByText(/30 \(71%\)/)).toBeInTheDocument();
  });

  it("renders barrier instances count", () => {
    render(<CaseManagerPage />);
    expect(screen.getByText(/120/)).toBeInTheDocument();
  });
});
