import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AssessPage from "../assess/page";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => ({ get: () => null }),
}));

// Mock API
vi.mock("@/lib/api", () => ({
  postAssessment: vi.fn(),
  postCredit: vi.fn(),
}));

// Mock resume extraction
vi.mock("@/lib/resume", () => ({
  extractResumeText: vi.fn(),
}));

// Mock useCityConfig — top-level static mock (Montgomery AL). vi.doMock +
// vi.resetModules was order-dependent in CI parallel runs; the static
// mock matches the AL-only test scenarios reliably.
vi.mock("@/hooks/useCityConfig", () => ({
  useCityConfig: () => ({
    name: "Montgomery",
    state: "AL",
    location: "Montgomery, AL",
    zip_ranges: ["36101-36199"],
    loading: false,
  }),
}));

function renderWithClient(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("AssessPage city-aware ZIP validation", () => {
  it("accepts Montgomery ZIP (36104) when city is AL", async () => {
    const user = userEvent.setup();
    renderWithClient(<AssessPage />);

    const zipInput = screen.getByLabelText(/zip code/i);
    await user.type(zipInput, "36104");

    // Should NOT show error
    expect(screen.queryByText(/please enter a/i)).not.toBeInTheDocument();
  });

  it("shows error for Fort Worth ZIP when city is AL", async () => {
    const user = userEvent.setup();
    renderWithClient(<AssessPage />);

    const zipInput = screen.getByLabelText(/zip code/i);
    await user.type(zipInput, "76102");

    // Should show error for wrong city
    expect(screen.getByText(/please enter a/i)).toBeInTheDocument();
  });
});
