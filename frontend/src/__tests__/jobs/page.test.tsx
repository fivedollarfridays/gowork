import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import type {
  JobApplication,
  FunnelResult,
  ResumeVersionInfo,
} from "@/lib/api/jobApplications";

// Shared mock searchParams — token and session are read from here
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

// Mock the jobApplications API module — all functions are vi.fn() we control per-test
vi.mock("@/lib/api/jobApplications", async () => {
  return {
    listApplications: vi.fn(),
    updateApplicationStatus: vi.fn(),
    getFunnel: vi.fn(),
    listResumeVersions: vi.fn(),
  };
});

import JobsPage from "@/app/jobs/page";
import * as apiMod from "@/lib/api/jobApplications";

const api = apiMod as unknown as {
  listApplications: ReturnType<typeof vi.fn>;
  updateApplicationStatus: ReturnType<typeof vi.fn>;
  getFunnel: ReturnType<typeof vi.fn>;
  listResumeVersions: ReturnType<typeof vi.fn>;
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <TranslationProvider>
        <JobsPage />
      </TranslationProvider>
    </QueryClientProvider>,
  );
}

function makeApp(overrides: Partial<JobApplication> = {}): JobApplication {
  return {
    id: 1,
    session_id: "sess-1",
    match_source: "twc",
    match_url: "https://example.com/job/1",
    company: "Acme",
    role: "Janitor",
    resume_version_id: null,
    status: "applied",
    applied_date: "2026-04-10",
    created_at: "2026-04-10T12:00:00Z",
    ...overrides,
  };
}

function makeFunnel(overrides: Partial<FunnelResult> = {}): FunnelResult {
  return {
    counts: {
      draft: 0,
      applied: 0,
      interview: 0,
      offer: 0,
      rejected: 0,
      withdrawn: 0,
    },
    draft_to_applied_rate: null,
    applied_to_interview_rate: null,
    interview_to_offer_rate: null,
    ...overrides,
  };
}

function makeVersion(
  overrides: Partial<ResumeVersionInfo> = {},
): ResumeVersionInfo {
  return {
    version_id: 42,
    session_id: "sess-1",
    doc_type: "resume",
    version_counter: 1,
    generation_method: "llm",
    use_counter: 1,
    created_at: "2026-04-10T12:00:00Z",
    ...overrides,
  };
}

beforeEach(() => {
  setLocale("en");
  mockSearchParams.set("session", "sess-1");
  mockSearchParams.set("token", "tkn");
  sessionStorage.clear();
  vi.clearAllMocks();

  api.listApplications.mockResolvedValue([]);
  api.getFunnel.mockResolvedValue(makeFunnel());
  api.listResumeVersions.mockResolvedValue([]);
  api.updateApplicationStatus.mockImplementation(
    async (id: number, status: string) => makeApp({ id, status: status as JobApplication["status"] }),
  );
});

afterEach(() => {
  mockSearchParams.delete("session");
  mockSearchParams.delete("token");
});

describe("JobsPage: header and shell", () => {
  it("renders page title and subtitle", async () => {
    renderPage();
    expect(
      await screen.findByRole("heading", { name: /jobs tracker/i, level: 1 }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/track applications from draft to offer/i),
    ).toBeInTheDocument();
  });

  it("shows missing-session message when session is absent", async () => {
    mockSearchParams.delete("session");
    mockSearchParams.delete("token");
    renderPage();
    expect(
      await screen.findByText(/no session available/i),
    ).toBeInTheDocument();
  });
});

describe("JobsPage: kanban columns", () => {
  it("renders all six status columns", async () => {
    renderPage();
    expect(await screen.findByTestId("column-draft")).toBeInTheDocument();
    expect(screen.getByTestId("column-applied")).toBeInTheDocument();
    expect(screen.getByTestId("column-interview")).toBeInTheDocument();
    expect(screen.getByTestId("column-offer")).toBeInTheDocument();
    expect(screen.getByTestId("column-rejected")).toBeInTheDocument();
    expect(screen.getByTestId("column-withdrawn")).toBeInTheDocument();
  });

  it("shows empty-board hint when no applications exist", async () => {
    renderPage();
    expect(
      await screen.findByText(/no applications yet/i),
    ).toBeInTheDocument();
  });

  it("renders cards grouped by status", async () => {
    api.listApplications.mockResolvedValue([
      makeApp({ id: 1, role: "Cashier", status: "applied" }),
      makeApp({ id: 2, role: "Line Cook", status: "interview" }),
      makeApp({ id: 3, role: "Warehouse", status: "draft" }),
    ]);
    renderPage();

    // Wait for cards to render (applications query resolves async).
    await screen.findByText(/cashier/i);

    const applied = screen.getByTestId("column-applied");
    expect(within(applied).getByText(/cashier/i)).toBeInTheDocument();

    const interview = screen.getByTestId("column-interview");
    expect(within(interview).getByText(/line cook/i)).toBeInTheDocument();

    const draft = screen.getByTestId("column-draft");
    expect(within(draft).getByText(/warehouse/i)).toBeInTheDocument();
  });
});

describe("JobsPage: status transitions", () => {
  it("clicking the card move menu triggers updateApplicationStatus", async () => {
    api.listApplications.mockResolvedValue([
      makeApp({ id: 5, role: "Forklift Operator", status: "applied" }),
    ]);
    renderPage();

    // Open move menu for the card
    const moveBtn = await screen.findByRole("button", {
      name: /move application: forklift operator/i,
    });
    await userEvent.click(moveBtn);

    // Dialog appears
    const dialog = await screen.findByRole("dialog", {
      name: /change status/i,
    });
    await userEvent.click(
      within(dialog).getByRole("button", { name: /^interview$/i }),
    );

    await waitFor(() => {
      expect(api.updateApplicationStatus).toHaveBeenCalledTimes(1);
    });
    const [id, status, token] = api.updateApplicationStatus.mock.calls[0];
    expect(id).toBe(5);
    expect(status).toBe("interview");
    expect(token).toBe("tkn");
  });

  it("surfaces a transition error when the API rejects the status change", async () => {
    api.listApplications.mockResolvedValue([
      makeApp({ id: 6, role: "Valet", status: "draft" }),
    ]);
    api.updateApplicationStatus.mockRejectedValueOnce(
      new Error("invalid transition"),
    );
    renderPage();

    await userEvent.click(
      await screen.findByRole("button", {
        name: /move application: valet/i,
      }),
    );
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(
      within(dialog).getByRole("button", { name: /^offer$/i }),
    );

    await waitFor(() => {
      const alerts = screen.getAllByRole("alert");
      expect(alerts.length).toBeGreaterThanOrEqual(1);
    });
  });
});

describe("JobsPage: resume version + generation method badge", () => {
  it("renders the generation-method badge for a card's resume version", async () => {
    api.listApplications.mockResolvedValue([
      makeApp({ id: 10, resume_version_id: 42, role: "Dispatcher" }),
    ]);
    api.listResumeVersions.mockResolvedValue([
      makeVersion({ version_id: 42, generation_method: "llm" }),
    ]);
    renderPage();

    expect(await screen.findByTestId("gen-method-10")).toHaveTextContent(
      /ai-generated/i,
    );
  });

  it("renders a resume version link when resume_version_id is set", async () => {
    api.listApplications.mockResolvedValue([
      makeApp({ id: 11, resume_version_id: 99, role: "Greeter" }),
    ]);
    api.listResumeVersions.mockResolvedValue([
      makeVersion({
        version_id: 99,
        generation_method: "template",
        version_counter: 3,
      }),
    ]);
    renderPage();

    const link = await screen.findByRole("link", { name: /resume v3/i });
    expect(link).toHaveAttribute(
      "href",
      "/api/documents/resume/99/pdf",
    );
  });

  it("omits the badge when no resume version is attached", async () => {
    api.listApplications.mockResolvedValue([
      makeApp({ id: 12, resume_version_id: null }),
    ]);
    renderPage();

    await screen.findByTestId("column-applied");
    expect(screen.queryByTestId("gen-method-12")).not.toBeInTheDocument();
  });
});

describe("JobsPage: funnel sidebar", () => {
  it("renders funnel counts and conversion rates", async () => {
    api.getFunnel.mockResolvedValue(
      makeFunnel({
        counts: {
          draft: 1,
          applied: 4,
          interview: 2,
          offer: 1,
          rejected: 1,
          withdrawn: 0,
        },
        draft_to_applied_rate: 0.8,
        applied_to_interview_rate: 0.5,
        interview_to_offer_rate: 0.5,
      }),
    );
    renderPage();

    // Total = 1+4+2+1+1+0 = 9
    expect(await screen.findByTestId("funnel-total")).toHaveTextContent("9");
    expect(screen.getByTestId("funnel-count-draft")).toHaveTextContent("1");
    expect(screen.getByTestId("funnel-count-applied")).toHaveTextContent("4");
    expect(screen.getByTestId("funnel-count-interview")).toHaveTextContent(
      "2",
    );
    expect(screen.getByTestId("funnel-count-offer")).toHaveTextContent("1");

    expect(
      screen.getByTestId("funnel-rate-draftToApplied"),
    ).toHaveTextContent(/80\s*%/);
    expect(
      screen.getByTestId("funnel-rate-appliedToInterview"),
    ).toHaveTextContent(/50\s*%/);
    expect(
      screen.getByTestId("funnel-rate-interviewToOffer"),
    ).toHaveTextContent(/50\s*%/);
  });

  it("renders 'no conversion data yet' when all rates are null", async () => {
    api.getFunnel.mockResolvedValue(makeFunnel());
    renderPage();
    expect(
      await screen.findByText(/no conversion data yet/i),
    ).toBeInTheDocument();
  });
});

describe("JobsPage: api error handling", () => {
  it("renders load-failed message when listApplications rejects", async () => {
    api.listApplications.mockRejectedValue(new Error("boom"));
    renderPage();
    const alerts = await screen.findAllByRole("alert");
    expect(
      alerts.some((el) => /failed to load applications/i.test(el.textContent ?? "")),
    ).toBe(true);
  });
});
