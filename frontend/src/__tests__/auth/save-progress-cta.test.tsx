import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api/auth", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/auth")>(
    "@/lib/api/auth",
  );
  return {
    ...actual,
    requestMagicLink: vi.fn(),
    getAccountMe: vi.fn(),
  };
});

import { requestMagicLink, getAccountMe } from "@/lib/api/auth";
import { SaveProgressCTA } from "@/components/auth/SaveProgressCTA";

const mockedRequestMagicLink = requestMagicLink as ReturnType<typeof vi.fn>;
const mockedGetAccountMe = getAccountMe as ReturnType<typeof vi.fn>;

function renderCTA(props: { dismissKey?: string } = {}) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0 },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={client}>
      <SaveProgressCTA dismissKey={props.dismissKey ?? "test-page"} />
    </QueryClientProvider>,
  );
}

describe("SaveProgressCTA", () => {
  beforeEach(() => {
    mockedRequestMagicLink.mockReset();
    mockedGetAccountMe.mockReset();
    // Default to anonymous so the CTA renders.
    mockedGetAccountMe.mockResolvedValue({ accountId: null, email: null });
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("renders 'Save your progress' card with email form for anonymous users", async () => {
    renderCTA();
    expect(
      await screen.findByRole("heading", { name: /save your progress/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /save my progress|send magic link/i }),
    ).toBeInTheDocument();
  });

  it("does not render when the account query says the user is claimed", async () => {
    mockedGetAccountMe.mockResolvedValueOnce({
      accountId: 7,
      email: "claimed@example.com",
    });
    const { container } = renderCTA();
    // After the query resolves the component should hide itself.
    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it("submits the form, calls requestMagicLink, then shows 'check your email' state", async () => {
    mockedRequestMagicLink.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderCTA();
    await screen.findByRole("heading", { name: /save your progress/i });

    await user.type(screen.getByLabelText(/email/i), "u@example.com");
    await user.click(
      screen.getByRole("button", { name: /save my progress|send magic link/i }),
    );

    await waitFor(() => {
      expect(screen.getByText(/check your (email|inbox)/i)).toBeInTheDocument();
    });
    expect(mockedRequestMagicLink).toHaveBeenCalledWith("u@example.com");
  });

  it("shows the same success state even when the request rejects (no enumeration)", async () => {
    mockedRequestMagicLink.mockRejectedValueOnce(new Error("rate limited"));
    const user = userEvent.setup();
    renderCTA();
    await screen.findByRole("heading", { name: /save your progress/i });

    await user.type(screen.getByLabelText(/email/i), "u@example.com");
    await user.click(
      screen.getByRole("button", { name: /save my progress|send magic link/i }),
    );

    await waitFor(() => {
      expect(screen.getByText(/check your (email|inbox)/i)).toBeInTheDocument();
    });
  });

  it("dismisses on X click and writes a localStorage key with that page's dismissKey", async () => {
    const user = userEvent.setup();
    const { container } = renderCTA({ dismissKey: "assess-page" });
    await screen.findByRole("heading", { name: /save your progress/i });

    await user.click(screen.getByRole("button", { name: /dismiss/i }));

    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
    const stored = window.localStorage.getItem(
      "gw_save_progress_cta_dismissed_assess-page",
    );
    expect(stored).not.toBeNull();
    // Stored value should be a numeric timestamp (milliseconds since epoch).
    expect(Number(stored)).toBeGreaterThan(0);
  });

  it("stays hidden when a recent dismissal exists in localStorage", async () => {
    window.localStorage.setItem(
      "gw_save_progress_cta_dismissed_assess-page",
      String(Date.now()),
    );
    const { container } = renderCTA({ dismissKey: "assess-page" });
    // Container should never grow children — the dismissal is read on
    // mount and the component returns null on the first render. We
    // give the query a chance to settle to keep the assertion stable.
    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it("re-renders when the stored dismissal is older than 24 hours", async () => {
    const twoDaysAgoMs = Date.now() - 2 * 24 * 60 * 60 * 1000;
    window.localStorage.setItem(
      "gw_save_progress_cta_dismissed_assess-page",
      String(twoDaysAgoMs),
    );
    renderCTA({ dismissKey: "assess-page" });
    expect(
      await screen.findByRole("heading", { name: /save your progress/i }),
    ).toBeInTheDocument();
  });

  it("disables submit until a non-empty email is entered", async () => {
    renderCTA();
    await screen.findByRole("heading", { name: /save your progress/i });
    const button = screen.getByRole("button", {
      name: /save my progress|send magic link/i,
    });
    expect(button).toBeDisabled();
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/email/i), "x@y.z");
    expect(button).not.toBeDisabled();
  });
});
