import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CreditPage from "../credit/page";

// Mock postCredit to simulate errors
vi.mock("@/lib/api", () => ({
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

function fillForm() {
  const inputs = screen.getAllByRole("spinbutton");
  // Credit Score, Utilization, Payment History, Account Age (required fields)
  fireEvent.change(inputs[0], { target: { value: "650" } });
  fireEvent.change(inputs[1], { target: { value: "30" } });
  fireEvent.change(inputs[2], { target: { value: "95" } });
  fireEvent.change(inputs[3], { target: { value: "24" } });
}

describe("CreditPage error handling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows error message and Try Again button on mutation failure", async () => {
    const { postCredit } = await import("@/lib/api");
    (postCredit as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Network error"),
    );

    renderWithClient(<CreditPage />);
    fillForm();

    // Submit form
    fireEvent.click(screen.getByRole("button", { name: /assess credit/i }));

    // Wait for error state
    const errorAlert = await screen.findByRole("alert");
    expect(errorAlert).toBeInTheDocument();
    expect(errorAlert).toHaveTextContent("Network error");

    // Retry button is present
    const retryBtn = screen.getByRole("button", { name: /try again/i });
    expect(retryBtn).toBeInTheDocument();
  });

  it("resets error state when Try Again is clicked", async () => {
    const { postCredit } = await import("@/lib/api");
    (postCredit as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Server error"),
    );

    renderWithClient(<CreditPage />);
    fillForm();

    // Submit and wait for error
    fireEvent.click(screen.getByRole("button", { name: /assess credit/i }));
    await screen.findByRole("alert");

    // Click Try Again — resets the mutation
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));

    // Error should be gone after React re-render
    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
  });
});
