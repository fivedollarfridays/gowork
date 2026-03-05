import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PlanPage from "../plan/page";

// Mock next/navigation
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

// Mock API
vi.mock("@/lib/api", () => ({
  getPlan: vi.fn(),
  generateNarrative: vi.fn(),
  getJobs: vi.fn(),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("PlanPage error handling", () => {
  it("shows error state with link to /assess when no session ID", () => {
    mockSearchParams.delete("session");
    renderWithClient(<PlanPage />);

    expect(screen.getByText(/no session id provided/i)).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /start an assessment/i });
    expect(link).toHaveAttribute("href", "/assess");
  });

  it("shows error with link to /assess when API returns 404", async () => {
    mockSearchParams.set("session", "nonexistent-id");

    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("404 Not Found"),
    );

    renderWithClient(<PlanPage />);

    const errorMsg = await screen.findByText(/session not found/i);
    expect(errorMsg).toBeInTheDocument();

    const link = screen.getByRole("link", { name: /start a new assessment/i });
    expect(link).toHaveAttribute("href", "/assess");
  });

  it("shows generic error when API fails with non-404", async () => {
    mockSearchParams.set("session", "some-session-id");

    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Internal Server Error"),
    );

    renderWithClient(<PlanPage />);

    const errorMsg = await screen.findByText(
      /something went wrong loading your plan/i,
    );
    expect(errorMsg).toBeInTheDocument();

    const link = screen.getByRole("link", { name: /start a new assessment/i });
    expect(link).toHaveAttribute("href", "/assess");
  });
});
