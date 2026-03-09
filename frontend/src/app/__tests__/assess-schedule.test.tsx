import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AssessPage from "../assess/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => ({ get: () => null }),
}));

vi.mock("@/lib/api", () => ({
  postAssessment: vi.fn(),
  postCredit: vi.fn(),
}));

vi.mock("@/lib/resume", () => ({
  extractResumeText: vi.fn(),
}));

// Skip framer-motion animations to prevent timeouts during multi-step navigation
vi.mock("framer-motion", async () => {
  const actual = await vi.importActual("framer-motion");
  return { ...actual, useReducedMotion: () => true };
});

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

async function advanceToScheduleStep(user: ReturnType<typeof userEvent.setup>) {
  renderWithClient(<AssessPage />);

  // Step 1: Enter valid ZIP
  const zipInput = screen.getByLabelText(/montgomery zip/i);
  await user.type(zipInput, "36104");

  // Step 1 -> 2 (Resume)
  await user.click(screen.getByRole("button", { name: /go to step 2/i }));
  // Step 2 -> 3 (Barriers)
  await user.click(screen.getByRole("button", { name: /go to step 3/i }));

  // Select a barrier so we can advance
  const creditCard = screen.getByText("Credit / Financial").closest("[role='button']")!;
  await user.click(creditCard);

  // Step 3 -> 4 (Benefits)
  await user.click(screen.getByRole("button", { name: /go to step 4/i }));
  // Step 4 -> 5 (Schedule)
  await user.click(screen.getByRole("button", { name: /go to step 5/i }));
}

describe("AssessPage schedule step", () => {
  it("renders schedule step with heading", { timeout: 15_000 }, async () => {
    const user = userEvent.setup();
    await advanceToScheduleStep(user);

    expect(
      screen.getByRole("heading", { name: /when can you work/i }),
    ).toBeInTheDocument();
  });

  it("shows all four schedule options", { timeout: 15_000 }, async () => {
    const user = userEvent.setup();
    await advanceToScheduleStep(user);

    // Open the schedule select dropdown
    const trigger = screen.getByRole("combobox", { name: /available hours/i });
    await user.click(trigger);

    // All 4 options should be present
    const listbox = screen.getByRole("listbox");
    expect(within(listbox).getByText(/daytime/i)).toBeInTheDocument();
    expect(within(listbox).getByText(/evening/i)).toBeInTheDocument();
    expect(within(listbox).getByText(/overnight/i)).toBeInTheDocument();
    expect(within(listbox).getByText(/flexible/i)).toBeInTheDocument();
  });

  it("defaults to daytime", { timeout: 15_000 }, async () => {
    const user = userEvent.setup();
    await advanceToScheduleStep(user);

    const trigger = screen.getByRole("combobox", { name: /available hours/i });
    expect(trigger).toHaveTextContent(/daytime/i);
  });

  it("shows schedule in review summary", { timeout: 15_000 }, async () => {
    const user = userEvent.setup();

    // Use a flow WITHOUT credit barrier to simplify navigation
    renderWithClient(<AssessPage />);

    const zipInput = screen.getByLabelText(/montgomery zip/i);
    await user.type(zipInput, "36104");

    // Step 1 -> 2 (Resume)
    await user.click(screen.getByRole("button", { name: /go to step 2/i }));
    // Step 2 -> 3 (Barriers)
    await user.click(screen.getByRole("button", { name: /go to step 3/i }));

    // Select transportation (not credit) so no Credit Check step
    const transportCard = screen.getByText("Transportation").closest("[role='button']")!;
    await user.click(transportCard);

    // Step 3 -> 4 (Benefits)
    await user.click(screen.getByRole("button", { name: /go to step 4/i }));
    // Step 4 -> 5 (Schedule)
    await user.click(screen.getByRole("button", { name: /go to step 5/i }));
    // Step 5 -> 6 (Industries)
    await user.click(screen.getByRole("button", { name: /go to step 6/i }));
    // Step 6 -> 7 (Review & Submit — no credit barrier)
    await user.click(screen.getByRole("button", { name: /go to step 7/i }));

    // Review summary should show default schedule value
    const summarySection = screen.getByText("Your Assessment Summary").closest("div")!;
    expect(within(summarySection).getByText("Schedule")).toBeInTheDocument();
    expect(within(summarySection).getByText("daytime")).toBeInTheDocument();
  });
});
