import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { FeedbackForm } from "../feedback/[token]/feedback-form";

// Mock api module
vi.mock("@/lib/api", () => ({
  validateFeedbackToken: vi.fn(),
  submitVisitFeedback: vi.fn(),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("FeedbackPage", () => {
  it("renders loading state while validating token", async () => {
    const { validateFeedbackToken } = await import("@/lib/api");
    (validateFeedbackToken as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}));

    renderWithClient(<FeedbackForm token="abc123" />);

    expect(screen.getByLabelText(/loading/i)).toBeInTheDocument();
  });

  it("shows error state for invalid/expired token", async () => {
    const { validateFeedbackToken } = await import("@/lib/api");
    (validateFeedbackToken as ReturnType<typeof vi.fn>).mockRejectedValue(new Error("Token expired"));

    renderWithClient(<FeedbackForm token="expired-tok" />);

    await waitFor(() => {
      expect(screen.getByText(/expired|invalid/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: /start a new assessment/i })).toHaveAttribute("href", "/assess");
  });

  it("renders 3-question form when token is valid", async () => {
    const { validateFeedbackToken } = await import("@/lib/api");
    (validateFeedbackToken as ReturnType<typeof vi.fn>).mockResolvedValue({ valid: true, session_id: "sess-1" });

    renderWithClient(<FeedbackForm token="valid-tok" />);

    await waitFor(() => {
      expect(screen.getByText(/did you make it/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/did montgowork/i)).toBeInTheDocument();
  });

  it("shows conditional Q2 when user selects Yes for Q1", async () => {
    const { validateFeedbackToken } = await import("@/lib/api");
    (validateFeedbackToken as ReturnType<typeof vi.fn>).mockResolvedValue({ valid: true, session_id: "sess-1" });

    renderWithClient(<FeedbackForm token="valid-tok" />);

    await waitFor(() => {
      expect(screen.getByText(/did you make it/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("radio", { name: /^Yes$/i }));

    await waitFor(() => {
      expect(screen.getByText(/what happened/i)).toBeInTheDocument();
    });
  });

  it("submits feedback and shows thank you", async () => {
    const { validateFeedbackToken, submitVisitFeedback } = await import("@/lib/api");
    (validateFeedbackToken as ReturnType<typeof vi.fn>).mockResolvedValue({ valid: true, session_id: "sess-1" });
    (submitVisitFeedback as ReturnType<typeof vi.fn>).mockResolvedValue({ success: true });

    renderWithClient(<FeedbackForm token="valid-tok" />);

    await waitFor(() => {
      expect(screen.getByText(/did you make it/i)).toBeInTheDocument();
    });

    // Answer Q1: Not yet
    fireEvent.click(screen.getByRole("radio", { name: /not yet/i }));
    // Answer Q3: Yes, it was helpful
    fireEvent.click(screen.getByRole("radio", { name: /yes, it was helpful/i }));
    // Submit
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/thank you/i)).toBeInTheDocument();
    });

    expect((submitVisitFeedback as ReturnType<typeof vi.fn>).mock.calls[0][0]).toEqual({
      token: "valid-tok",
      made_it_to_center: 1,
      outcomes: [],
      plan_accuracy: 3,
      free_text: "",
    });
  });

  it("shows already submitted state on duplicate", async () => {
    const { validateFeedbackToken, submitVisitFeedback } = await import("@/lib/api");
    (validateFeedbackToken as ReturnType<typeof vi.fn>).mockResolvedValue({ valid: true, session_id: "sess-1" });
    (submitVisitFeedback as ReturnType<typeof vi.fn>).mockRejectedValue(new Error("Feedback already submitted"));

    renderWithClient(<FeedbackForm token="valid-tok" />);

    await waitFor(() => {
      expect(screen.getByText(/did you make it/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("radio", { name: /not yet/i }));
    fireEvent.click(screen.getByRole("radio", { name: /yes, it was helpful/i }));
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/already submitted/i)).toBeInTheDocument();
    });
  });

  it("has large touch targets on radio labels", async () => {
    const { validateFeedbackToken } = await import("@/lib/api");
    (validateFeedbackToken as ReturnType<typeof vi.fn>).mockResolvedValue({ valid: true, session_id: "sess-1" });

    renderWithClient(<FeedbackForm token="valid-tok" />);

    await waitFor(() => {
      expect(screen.getByText(/did you make it/i)).toBeInTheDocument();
    });

    const radios = screen.getAllByRole("radio");
    for (const radio of radios) {
      const label = radio.closest("label");
      expect(label).toBeTruthy();
      expect(label?.className).toMatch(/min-h-11|min-h-\[44px\]/);
    }
  });
});
