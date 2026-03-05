import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AssessPage from "../assess/page";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// Mock API
vi.mock("@/lib/api", () => ({
  postAssessment: vi.fn(),
  postCredit: vi.fn(),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("AssessPage barrier guidance", () => {
  it("shows guidance text when no barriers are selected", async () => {
    const user = userEvent.setup();
    renderWithClient(<AssessPage />);

    // Enter valid ZIP to advance past step 1
    const zipInput = screen.getByLabelText(/montgomery zip/i);
    await user.type(zipInput, "36104");

    // Advance to Barriers step
    const nextBtn = screen.getByRole("button", { name: /go to step 2/i });
    await user.click(nextBtn);

    // Guidance text visible when no barriers selected
    expect(
      screen.getByText(/select at least one barrier to continue/i),
    ).toBeInTheDocument();
  });

  it("hides guidance text after selecting a barrier", async () => {
    const user = userEvent.setup();
    renderWithClient(<AssessPage />);

    // Enter valid ZIP
    const zipInput = screen.getByLabelText(/montgomery zip/i);
    await user.type(zipInput, "36104");

    // Advance to Barriers step
    const nextBtn = screen.getByRole("button", { name: /go to step 2/i });
    await user.click(nextBtn);

    // Click a barrier card (they're rendered as role="button" cards)
    const creditCard = screen.getByText("Credit / Financial").closest("[role='button']")!;
    await user.click(creditCard);

    // Guidance text should be gone
    expect(
      screen.queryByText(/select at least one barrier to continue/i),
    ).not.toBeInTheDocument();
  });
});
