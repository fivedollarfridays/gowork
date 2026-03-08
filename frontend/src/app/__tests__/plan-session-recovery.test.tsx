import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import PlanPage from "../plan/page";

// Mock next/navigation — shared mutable instance
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

describe("PlanPage session recovery", () => {
  beforeEach(() => {
    mockSearchParams.delete("session");
    localStorage.clear();
  });

  it("stores session ID from URL to localStorage", () => {
    mockSearchParams.set("session", "sess-abc-123");
    renderWithClient(<PlanPage />);

    expect(localStorage.getItem("montgowork_session_id")).toBe("sess-abc-123");
  });

  it("recovers session ID from localStorage when URL param is missing", async () => {
    localStorage.setItem("montgowork_session_id", "sess-recovered");

    const { getPlan } = await import("@/lib/api");
    (getPlan as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("404 Not Found"),
    );

    renderWithClient(<PlanPage />);

    // Should NOT show "No session ID provided" — it recovered from localStorage
    expect(screen.queryByText(/no session id provided/i)).not.toBeInTheDocument();
  });

  it("shows error when both URL param and localStorage are empty", () => {
    // No URL param, no localStorage
    renderWithClient(<PlanPage />);

    expect(screen.getByText(/no session id provided/i)).toBeInTheDocument();
  });
});
