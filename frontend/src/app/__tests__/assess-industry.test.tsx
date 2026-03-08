import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AssessPage from "../assess/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/api", () => ({
  postAssessment: vi.fn(),
  postCredit: vi.fn(),
}));

vi.mock("@/lib/resume", () => ({
  extractResumeText: vi.fn(),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

async function advanceToIndustryStep(user: ReturnType<typeof userEvent.setup>) {
  renderWithClient(<AssessPage />);
  const zipInput = screen.getByLabelText(/montgomery zip/i);
  await user.type(zipInput, "36104");

  // Step 1 -> 2 (Resume)
  await user.click(screen.getByRole("button", { name: /go to step 2/i }));
  // Step 2 -> 3 (Barriers)
  await user.click(screen.getByRole("button", { name: /go to step 3/i }));

  // Select a barrier to advance
  const transportCard = screen.getByText("Transportation").closest("[role='button']")!;
  await user.click(transportCard);

  // Step 3 -> 4 (Schedule)
  await user.click(screen.getByRole("button", { name: /go to step 4/i }));
  // Step 4 -> 5 (Industries)
  await user.click(screen.getByRole("button", { name: /go to step 5/i }));
}

describe("AssessPage industry step", () => {
  it("renders industry step heading", async () => {
    const user = userEvent.setup();
    await advanceToIndustryStep(user);

    expect(
      screen.getByRole("heading", { name: /target industries/i }),
    ).toBeInTheDocument();
  });

  it("shows all 7 industry options", async () => {
    const user = userEvent.setup();
    await advanceToIndustryStep(user);

    expect(screen.getByText("Healthcare")).toBeInTheDocument();
    expect(screen.getByText("Manufacturing")).toBeInTheDocument();
    expect(screen.getByText("Food Service")).toBeInTheDocument();
    expect(screen.getByText("Government")).toBeInTheDocument();
    expect(screen.getByText("Retail")).toBeInTheDocument();
    expect(screen.getByText("Construction")).toBeInTheDocument();
    expect(screen.getByText("Transportation")).toBeInTheDocument();
  });

  it("shows certification checkboxes", async () => {
    const user = userEvent.setup();
    await advanceToIndustryStep(user);

    expect(screen.getByText(/do you have any of these certifications/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/CNA/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/CDL/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/LPN/i)).toBeInTheDocument();
  });

  it("can advance without selecting (optional step)", async () => {
    const user = userEvent.setup();
    await advanceToIndustryStep(user);

    const nextBtn = screen.getByRole("button", { name: /go to step 6/i });
    expect(nextBtn).not.toBeDisabled();
  });

  it("toggles industry selection", async () => {
    const user = userEvent.setup();
    await advanceToIndustryStep(user);

    const healthcareCard = screen.getByText("Healthcare").closest("[role='button']")!;
    await user.click(healthcareCard);

    // Card should have selected styling (ring class)
    expect(healthcareCard).toHaveClass("ring-1");
  });
});
