import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import CaseManagerPage from "../page";
import { useQuery } from "@tanstack/react-query";
import { TranslationProvider } from "@/hooks/useTranslation";

function renderPage() {
  return render(
    <TranslationProvider>
      <CaseManagerPage />
    </TranslationProvider>,
  );
}

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
    renderPage();
    expect(screen.getByText(/Case Manager Dashboard/i)).toBeInTheDocument();
  });

  it("shows total assessments", () => {
    renderPage();
    expect(screen.getByText(/42/)).toBeInTheDocument();
  });

  it("shows common barriers", () => {
    renderPage();
    expect(screen.getByText(/credit/i)).toBeInTheDocument();
    expect(screen.getByText(/transportation/i)).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (useQuery as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
    renderPage();
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    (useQuery as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Server down"),
    });
    renderPage();
    expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
  });

  it("computes average barriers per person", () => {
    renderPage();
    // 120 / 42 = 2.857... rounded to 2.9
    expect(screen.getByText("2.9")).toBeInTheDocument();
  });

  it("shows barrier percentage in bar chart", () => {
    renderPage();
    // credit: 30/42 = 71%
    expect(screen.getByText(/30 \(71%\)/)).toBeInTheDocument();
  });

  it("renders barrier instances count", () => {
    renderPage();
    expect(screen.getByText(/120/)).toBeInTheDocument();
  });

  it("does not render the Needs Attention section when no advisor token is stored", () => {
    window.sessionStorage.clear();
    renderPage();
    expect(screen.queryByText(/Needs Attention/i)).toBeNull();
  });

  it("renders the Needs Attention section when an advisor token is stored", () => {
    window.sessionStorage.setItem(
      "montgowork_advisor_token", "mw_adv_test",
    );
    (useQuery as ReturnType<typeof vi.fn>).mockImplementation(
      (opts: { queryKey: unknown[] }) => {
        const key = (opts.queryKey ?? [])[0];
        if (key === "advisor-stalled") {
          return {
            data: { sessions: [] }, isLoading: false, error: null,
          };
        }
        return {
          data: {
            total_assessments: 42,
            total_barrier_instances: 120,
            common_barriers: [],
          },
          isLoading: false,
          error: null,
        };
      },
    );
    renderPage();
    expect(screen.getByText(/Needs Attention/i)).toBeInTheDocument();
  });
});
