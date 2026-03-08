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

const mockExtract = vi.fn();
vi.mock("@/lib/resume", () => ({
  extractResumeText: (...args: unknown[]) => mockExtract(...args),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

async function advanceToResumeStep(user: ReturnType<typeof userEvent.setup>) {
  renderWithClient(<AssessPage />);
  const zipInput = screen.getByLabelText(/montgomery zip/i);
  await user.type(zipInput, "36104");
  // Step 1 -> 2 (Resume)
  await user.click(screen.getByRole("button", { name: /go to step 2/i }));
}

describe("AssessPage resume step", () => {
  it("renders resume step heading", async () => {
    const user = userEvent.setup();
    await advanceToResumeStep(user);

    expect(
      screen.getByRole("heading", { name: /upload your resume/i }),
    ).toBeInTheDocument();
  });

  it("shows skip messaging", async () => {
    const user = userEvent.setup();
    await advanceToResumeStep(user);

    expect(
      screen.getByText(/don't have a resume/i),
    ).toBeInTheDocument();
  });

  it("can advance without uploading (optional step)", async () => {
    const user = userEvent.setup();
    await advanceToResumeStep(user);

    // Next button should be enabled (step is optional)
    const nextBtn = screen.getByRole("button", { name: /go to step 3/i });
    expect(nextBtn).not.toBeDisabled();
  });

  it("shows drop zone for file upload", async () => {
    const user = userEvent.setup();
    await advanceToResumeStep(user);

    expect(
      screen.getByText(/drop your resume here/i),
    ).toBeInTheDocument();
  });
});
