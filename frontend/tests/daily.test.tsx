import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import axe from "axe-core";

// Shared mock searchParams — session and token read from here
const mockSearchParams = new URLSearchParams();
const mockRouter = { push: vi.fn(), replace: vi.fn(), back: vi.fn() };
vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
  useRouter: () => mockRouter,
}));

// Mock the digest API module
vi.mock("@/lib/api/digest", async () => {
  return {
    previewDigest: vi.fn(),
    parseDigestSections: (await vi.importActual<
      typeof import("@/lib/api/digest")
    >("@/lib/api/digest")).parseDigestSections,
  };
});

import DailyPage from "@/app/daily/page";
import HomePage from "@/app/page";
import * as digestApi from "@/lib/api/digest";

const api = digestApi as unknown as {
  previewDigest: ReturnType<typeof vi.fn>;
  parseDigestSections: (
    text: string,
  ) => { yesterday: string; today: string; week: string; stall: string };
};

type DigestResult = {
  subject: string;
  html: string;
  text: string;
  section_counts: {
    yesterday: number;
    today: number;
    week: number;
    stall: number;
  };
};

function buildDigest(overrides: Partial<DigestResult> = {}): DigestResult {
  return {
    subject: "[MontGoWork] Your daily digest — Thursday, Apr 23",
    html: "<p>Hi friend,</p>",
    text: [
      "Hi friend,",
      "",
      "Yesterday",
      "1 appointment attended:",
      "- Credit coach meeting",
      "",
      "Today",
      "09:00: Interview at Acme — at Acme HQ",
      "",
      "This week",
      "",
      "Check-in",
      "Quick check-in — about 3 days since your last update. Everything still on track?",
      "",
    ].join("\n"),
    section_counts: { yesterday: 1, today: 1, week: 0, stall: 1 },
    ...overrides,
  };
}

function renderDaily() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <TranslationProvider>
        <DailyPage />
      </TranslationProvider>
    </QueryClientProvider>,
  );
}

function renderHome() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <TranslationProvider>
        <HomePage />
      </TranslationProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  setLocale("en");
  mockSearchParams.set("session", "sess-1");
  mockSearchParams.set("token", "tkn");
  sessionStorage.clear();
  vi.clearAllMocks();
  mockRouter.replace.mockClear();
  mockRouter.push.mockClear();
});

afterEach(() => {
  mockSearchParams.delete("session");
  mockSearchParams.delete("token");
});

describe("parseDigestSections", () => {
  it("splits text into yesterday/today/week/stall bodies", () => {
    const text = [
      "Hi friend,",
      "",
      "Yesterday",
      "1 appointment attended:",
      "- Coach",
      "",
      "Today",
      "09:00: Interview",
      "",
      "This week",
      "No events",
      "",
      "Check-in",
      "Quick check-in — about 3 days",
      "",
    ].join("\n");
    const result = api.parseDigestSections(text);
    expect(result.yesterday).toContain("1 appointment attended");
    expect(result.yesterday).toContain("- Coach");
    expect(result.today).toContain("09:00: Interview");
    expect(result.week).toContain("No events");
    expect(result.stall).toContain("Quick check-in");
  });

  it("returns empty strings when section headers missing", () => {
    const result = api.parseDigestSections("Hi friend,\n\nNothing new today.");
    expect(result.yesterday).toBe("");
    expect(result.today).toBe("");
    expect(result.week).toBe("");
    expect(result.stall).toBe("");
  });
});

describe("DailyPage: loading + empty states", () => {
  it("renders loading state initially", () => {
    api.previewDigest.mockImplementation(() => new Promise(() => {}));
    renderDaily();
    expect(screen.getByText(/loading your digest/i)).toBeInTheDocument();
  });

  it("shows missing-session message when no session", async () => {
    mockSearchParams.delete("session");
    mockSearchParams.delete("token");
    renderDaily();
    expect(
      await screen.findByText(/session expired|log in again/i),
    ).toBeInTheDocument();
  });
});

describe("DailyPage: section rendering", () => {
  it("renders yesterday section when section_counts.yesterday > 0", async () => {
    api.previewDigest.mockResolvedValue(buildDigest());
    renderDaily();
    expect(
      await screen.findByRole("heading", { name: /yesterday/i }),
    ).toBeInTheDocument();
  });

  it("omits yesterday section when section_counts.yesterday == 0", async () => {
    api.previewDigest.mockResolvedValue(
      buildDigest({
        section_counts: { yesterday: 0, today: 1, week: 0, stall: 0 },
        text: [
          "Hi friend,",
          "",
          "Today",
          "09:00: Interview",
          "",
        ].join("\n"),
      }),
    );
    renderDaily();
    await screen.findByRole("heading", { name: /today/i });
    expect(
      screen.queryByRole("heading", { name: /yesterday/i }),
    ).not.toBeInTheDocument();
  });

  it("renders stall alert when section_counts.stall > 0 with link to barriers", async () => {
    api.previewDigest.mockResolvedValue(buildDigest());
    renderDaily();
    const stallHeading = await screen.findByRole("heading", {
      name: /needs attention/i,
    });
    expect(stallHeading).toBeInTheDocument();
    // Link to barriers deep-link
    const link = screen.getByRole("link", { name: /talk to a navigator|view barriers/i });
    expect(link).toHaveAttribute("href", expect.stringContaining("/plan"));
  });

  it("renders week 'coming soon' placeholder when week count is 0", async () => {
    api.previewDigest.mockResolvedValue(buildDigest());
    renderDaily();
    await screen.findByRole("heading", { name: /this week/i });
    expect(
      screen.getByText(/more community updates coming soon/i),
    ).toBeInTheDocument();
  });

  it("sections expand/collapse on click", async () => {
    api.previewDigest.mockResolvedValue(buildDigest());
    renderDaily();
    const yesterdayToggle = await screen.findByRole("button", {
      name: /yesterday/i,
    });
    // Default: expanded (count > 0) → body visible
    expect(screen.getByText(/1 appointment attended/i)).toBeInTheDocument();
    await userEvent.click(yesterdayToggle);
    // After click: collapsed
    await waitFor(() => {
      expect(
        screen.queryByText(/1 appointment attended/i),
      ).not.toBeInTheDocument();
    });
  });
});

describe("DailyPage: error handling", () => {
  it("handles 401 gracefully — shows unauthorized error", async () => {
    api.previewDigest.mockRejectedValue(new Error("Unauthorized (401)"));
    renderDaily();
    expect(
      await screen.findByText(/session expired|log in again/i),
    ).toBeInTheDocument();
  });

  it("handles 403 gracefully — shows generic error", async () => {
    api.previewDigest.mockRejectedValue(new Error("Forbidden (403)"));
    renderDaily();
    expect(
      await screen.findByText(/couldn't load your digest/i),
    ).toBeInTheDocument();
  });

  it("handles 500 gracefully — shows generic error", async () => {
    api.previewDigest.mockRejectedValue(new Error("Server error (500)"));
    renderDaily();
    expect(
      await screen.findByText(/couldn't load your digest/i),
    ).toBeInTheDocument();
  });
});

describe("DailyPage: a11y", () => {
  it("is free of axe-core violations", async () => {
    api.previewDigest.mockResolvedValue(buildDigest());
    const { container } = renderDaily();
    await screen.findByRole("heading", { name: /yesterday/i });
    const results = await axe.run(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });
});

describe("HomePage: conditional redirect", () => {
  it("unauthenticated user stays on home (no redirect)", () => {
    mockSearchParams.delete("session");
    mockSearchParams.delete("token");
    sessionStorage.clear();
    renderHome();
    expect(mockRouter.replace).not.toHaveBeenCalled();
  });

  it("mid-assessment user (session but no feedback token) stays on home", async () => {
    // Simulate: session exists, but no feedback token recorded → mid-assessment
    mockSearchParams.delete("token");
    sessionStorage.setItem("montgowork_session_id", "sess-1");
    renderHome();
    await waitFor(() => {
      // Give the useEffect a tick; should NOT redirect
      expect(mockRouter.replace).not.toHaveBeenCalled();
    });
  });

  it("post-assessment user (session + feedback_token in storage) redirects to /daily", async () => {
    mockSearchParams.delete("session");
    mockSearchParams.delete("token");
    sessionStorage.setItem("montgowork_session_id", "sess-1");
    sessionStorage.setItem("feedback_token_sess-1", "tok-xyz");
    renderHome();
    await waitFor(() => {
      expect(mockRouter.replace).toHaveBeenCalledWith("/daily");
    });
  });
});
