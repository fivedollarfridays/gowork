import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CoverLettersPage from "@/app/documents/cover-letters/page";

const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/lib/api/documents", () => ({
  listVersions: vi.fn(),
  generateCoverLetter: vi.fn(),
  getCoverLetterMarkdown: vi.fn(),
  resumePdfUrl: (id: number, token: string) =>
    `/api/documents/resume/${id}/pdf?token=${token}`,
  coverLetterPdfUrl: (id: number, token: string) =>
    `/api/documents/cover-letter/${id}/pdf?token=${token}`,
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

function setAuth(session: string, token: string) {
  mockSearchParams.set("session", session);
  mockSearchParams.set("token", token);
}

beforeEach(() => {
  mockSearchParams.delete("session");
  mockSearchParams.delete("token");
  sessionStorage.clear();
  vi.clearAllMocks();
});

describe("CoverLettersPage", () => {
  it("shows missing-session state when no session/token is present", async () => {
    renderWithClient(<CoverLettersPage />);
    await waitFor(() => {
      expect(screen.getByText(/no session available/i)).toBeInTheDocument();
    });
  });

  it("warns when there are no resume versions (user must generate one first)", async () => {
    setAuth("sess-1", "tkn");
    const api = await import("@/lib/api/documents");
    (api.listVersions as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderWithClient(<CoverLettersPage />);

    await waitFor(() => {
      expect(
        screen.getByText(/generate a resume first/i),
      ).toBeInTheDocument();
    });
    // The generate button should be disabled without a resume
    const btn = screen.getByRole("button", { name: /generate cover letter/i });
    expect(btn).toBeDisabled();
  });

  it("POSTs cover letter with resume_version_id + job_match_ref from the form", async () => {
    setAuth("sess-1", "tkn");
    const api = await import("@/lib/api/documents");
    (api.listVersions as ReturnType<typeof vi.fn>).mockResolvedValue([
      {
        version_id: 9,
        session_id: "sess-1",
        doc_type: "resume",
        version_counter: 2,
        generation_method: "template",
        use_counter: 0,
        created_at: "2026-04-22T12:00:00Z",
      },
    ]);
    (api.generateCoverLetter as ReturnType<typeof vi.fn>).mockResolvedValue({
      version_id: 50,
      version_counter: 1,
      session_id: "sess-1",
      doc_type: "cover_letter",
      generation_method: "template",
      fair_chance: false,
    });
    (api.getCoverLetterMarkdown as ReturnType<typeof vi.fn>).mockResolvedValue(
      "Dear Acme team,\n\n...",
    );

    renderWithClient(<CoverLettersPage />);

    const titleInput = await screen.findByLabelText(/job title/i);
    const companyInput = screen.getByLabelText(/company/i);
    await userEvent.type(titleInput, "Stocker");
    await userEvent.type(companyInput, "Acme");

    const btn = screen.getByRole("button", { name: /generate cover letter/i });
    await waitFor(() => expect(btn).not.toBeDisabled());
    await userEvent.click(btn);

    await waitFor(() => {
      expect(api.generateCoverLetter).toHaveBeenCalled();
    });
    const [payload, tok] = (api.generateCoverLetter as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(tok).toBe("tkn");
    expect(payload).toMatchObject({
      session_id: "sess-1",
      resume_version_id: 9,
      job_match_ref: expect.objectContaining({
        title: "Stocker",
        company: "Acme",
      }),
    });
  });

  it("shows cover-letter version history (filtered to cover_letter) with PDF link", async () => {
    setAuth("sess-1", "tkn");
    const api = await import("@/lib/api/documents");
    (api.listVersions as ReturnType<typeof vi.fn>).mockResolvedValue([
      {
        version_id: 50,
        session_id: "sess-1",
        doc_type: "cover_letter",
        version_counter: 1,
        generation_method: "template",
        use_counter: 0,
        created_at: "2026-04-22T12:00:00Z",
      },
      {
        version_id: 9,
        session_id: "sess-1",
        doc_type: "resume",
        version_counter: 2,
        generation_method: "template",
        use_counter: 0,
        created_at: "2026-04-21T12:00:00Z",
      },
    ]);

    renderWithClient(<CoverLettersPage />);

    await waitFor(() => {
      const pdfLinks = screen.getAllByRole("link", { name: /pdf/i });
      expect(pdfLinks).toHaveLength(1);
      expect(pdfLinks[0]).toHaveAttribute(
        "href",
        expect.stringMatching(/\/api\/documents\/cover-letter\/50\/pdf/),
      );
    });
  });

  it("shows an error message when generation fails", async () => {
    setAuth("sess-1", "tkn");
    const api = await import("@/lib/api/documents");
    (api.listVersions as ReturnType<typeof vi.fn>).mockResolvedValue([
      {
        version_id: 9,
        session_id: "sess-1",
        doc_type: "resume",
        version_counter: 1,
        generation_method: "template",
        use_counter: 0,
        created_at: "2026-04-22T12:00:00Z",
      },
    ]);
    (api.generateCoverLetter as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("LLM down"),
    );

    renderWithClient(<CoverLettersPage />);

    await userEvent.type(
      await screen.findByLabelText(/job title/i),
      "Stocker",
    );
    await userEvent.type(screen.getByLabelText(/company/i), "Acme");
    await userEvent.click(
      screen.getByRole("button", { name: /generate cover letter/i }),
    );

    await waitFor(() => {
      expect(
        screen.getByText(/could not generate the cover letter/i),
      ).toBeInTheDocument();
    });
  });
});
