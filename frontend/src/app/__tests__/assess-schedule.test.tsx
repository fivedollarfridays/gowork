import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
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

  // Advance to Barriers (step 2)
  const toBarriers = screen.getByRole("button", { name: /go to step 2/i });
  await user.click(toBarriers);

  // Select a barrier so we can advance
  const creditCard = screen.getByText("Credit / Financial").closest("[role='button']")!;
  await user.click(creditCard);

  // Advance to Schedule (step 3)
  const toSchedule = screen.getByRole("button", { name: /go to step 3/i });
  await user.click(toSchedule);
}

describe("AssessPage schedule step", () => {
  it("renders schedule step with heading", async () => {
    const user = userEvent.setup();
    await advanceToScheduleStep(user);

    expect(
      screen.getByRole("heading", { name: /when can you work/i }),
    ).toBeInTheDocument();
  });

  it("shows all four schedule options", async () => {
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

  it("defaults to daytime", async () => {
    const user = userEvent.setup();
    await advanceToScheduleStep(user);

    const trigger = screen.getByRole("combobox", { name: /available hours/i });
    expect(trigger).toHaveTextContent(/daytime/i);
  });

  it("shows schedule in review summary", async () => {
    const user = userEvent.setup();

    // Use a flow WITHOUT credit barrier to simplify navigation
    renderWithClient(<AssessPage />);

    const zipInput = screen.getByLabelText(/montgomery zip/i);
    await user.type(zipInput, "36104");

    // Advance to Barriers
    const toBarriers = screen.getByRole("button", { name: /go to step 2/i });
    await user.click(toBarriers);

    // Select transportation (not credit) so no Credit Check step
    const transportCard = screen.getByText("Transportation").closest("[role='button']")!;
    await user.click(transportCard);

    // Advance to Schedule
    const toSchedule = screen.getByRole("button", { name: /go to step 3/i });
    await user.click(toSchedule);

    // Advance to Review & Submit
    const toReview = screen.getByRole("button", { name: /go to step 4/i });
    await user.click(toReview);

    // Review summary should show default schedule value
    const summarySection = screen.getByText("Your Assessment Summary").closest("div")!;
    expect(within(summarySection).getByText("Schedule")).toBeInTheDocument();
    expect(within(summarySection).getByText("daytime")).toBeInTheDocument();
  });
});
