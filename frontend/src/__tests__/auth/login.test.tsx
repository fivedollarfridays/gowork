import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api/auth", () => ({
  requestMagicLink: vi.fn(),
}));

import { requestMagicLink } from "@/lib/api/auth";
import LoginPage from "@/app/auth/login/page";

const mockedRequestMagicLink = requestMagicLink as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <LoginPage />
    </QueryClientProvider>,
  );
}

describe("LoginPage (/auth/login)", () => {
  beforeEach(() => {
    mockedRequestMagicLink.mockReset();
  });

  it("renders the email form in idle state", () => {
    renderPage();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/sign in|log in/i);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send magic link/i })).toBeInTheDocument();
  });

  it("disables submit when email is empty", () => {
    renderPage();
    expect(screen.getByRole("button", { name: /send magic link/i })).toBeDisabled();
  });

  it("submits the form and shows the check-your-email confirmation", async () => {
    mockedRequestMagicLink.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderPage();
    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.click(screen.getByRole("button", { name: /send magic link/i }));
    await waitFor(() => {
      expect(screen.getByText(/check your (email|inbox)/i)).toBeInTheDocument();
    });
    expect(mockedRequestMagicLink).toHaveBeenCalledWith("user@example.com");
  });

  it("still shows the success screen when the API rejects (no enumeration)", async () => {
    mockedRequestMagicLink.mockRejectedValueOnce(new Error("rate limited"));
    const user = userEvent.setup();
    renderPage();
    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.click(screen.getByRole("button", { name: /send magic link/i }));
    await waitFor(() => {
      expect(screen.getByText(/check your (email|inbox)/i)).toBeInTheDocument();
    });
  });

  it("shows a loading indicator while the request is in flight", async () => {
    let resolve: (() => void) | undefined;
    mockedRequestMagicLink.mockImplementationOnce(
      () => new Promise<void>((r) => { resolve = () => r(); }),
    );
    const user = userEvent.setup();
    renderPage();
    await user.type(screen.getByLabelText(/email/i), "a@b.co");
    await user.click(screen.getByRole("button", { name: /send magic link/i }));
    await waitFor(() => {
      expect(screen.getByRole("button")).toBeDisabled();
    });
    resolve?.();
  });
});
