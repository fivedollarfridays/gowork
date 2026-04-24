import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ResumePage from "@/app/documents/resume/page";

const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/lib/api/documents", () => ({
  listVersions: vi.fn(),
  generateResume: vi.fn(),
  getResumeMarkdown: vi.fn(),
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

describe("ResumePage", () => {
  it("shows missing-session message when no session is available", async () => {
    renderWithClient(<ResumePage />);
    // The loading state may appear first but the final state shows missing session
    await waitFor(() => {
      expect(
        screen.getByText(/no session available/i),
      ).toBeInTheDocument();
    });
  });

  it("renders title, generate form, and empty version list when no versions exist", async () => {
    setAuth("sess-1", "tkn");
    const api = await import("@/lib/api/documents");
    (api.listVersions as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    renderWithClient(<ResumePage />);

    expect(
      await screen.findByRole("heading", { name: /resume/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /generate resume/i }),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(
        screen.getByText(/no resume versions yet/i),
      ).toBeInTheDocument();
    });
  });

  it("calls generateResume with job_description when Generate is clicked", async () => {
    setAuth("sess-1", "tkn");
    const api = await import("@/lib/api/documents");
    (api.listVersions as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (api.generateResume as ReturnType<typeof vi.fn>).mockResolvedValue({
      version_id: 7,
      version_counter: 1,
      session_id: "sess-1",
      doc_type: "resume",
      generation_method: "template",
    });
    (api.getResumeMarkdown as ReturnType<typeof vi.fn>).mockResolvedValue(
      "# My resume\nGenerated text.",
    );

    renderWithClient(<ResumePage />);

    await screen.findByRole("button", { name: /generate resume/i });

    const textarea = screen.getByLabelText(/target job/i) as HTMLTextAreaElement;
    await userEvent.type(textarea, "Warehouse associate");
    await userEvent.click(
      screen.getByRole("button", { name: /generate resume/i }),
    );

    await waitFor(() => {
      expect(api.generateResume).toHaveBeenCalledWith(
        {
          session_id: "sess-1",
          job_description: "Warehouse associate",
        },
        "tkn",
      );
    });
  });

  it("renders version list (newest-first) with PDF download link when versions exist", async () => {
    setAuth("sess-1", "tkn");
    const api = await import("@/lib/api/documents");
    (api.listVersions as ReturnType<typeof vi.fn>).mockResolvedValue([
      {
        version_id: 5,
        session_id: "sess-1",
        doc_type: "resume",
        version_counter: 2,
        generation_method: "llm",
        use_counter: 0,
        created_at: "2026-04-22T12:00:00Z",
      },
      {
        version_id: 3,
        session_id: "sess-1",
        doc_type: "resume",
        version_counter: 1,
        generation_method: "template",
        use_counter: 0,
        created_at: "2026-04-20T12:00:00Z",
      },
    ]);

    renderWithClient(<ResumePage />);

    await waitFor(() => {
      const pdfLinks = screen.getAllByRole("link", { name: /pdf/i });
      expect(pdfLinks).toHaveLength(2);
      expect(pdfLinks[0]).toHaveAttribute(
        "href",
        expect.stringMatching(/\/api\/documents\/resume\/5\/pdf\?token=tkn/),
      );
    });
  });

  it("shows error state when generateResume fails", async () => {
    setAuth("sess-1", "tkn");
    const api = await import("@/lib/api/documents");
    (api.listVersions as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (api.generateResume as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("server down"),
    );

    renderWithClient(<ResumePage />);

    await userEvent.click(
      await screen.findByRole("button", { name: /generate resume/i }),
    );

    await waitFor(() => {
      expect(
        screen.getByText(/could not generate the resume/i),
      ).toBeInTheDocument();
    });
  });
});
