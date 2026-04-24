import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import type { DocumentVersion } from "../documents";

describe("documents API client", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function mockJson(body: unknown, ok = true, status = 200) {
    fetchMock.mockResolvedValueOnce({
      ok,
      status,
      statusText: ok ? "OK" : "Error",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => body,
    });
  }

  function mockText(body: string, ok = true, status = 200) {
    fetchMock.mockResolvedValueOnce({
      ok,
      status,
      statusText: ok ? "OK" : "Error",
      headers: new Headers({ "content-type": "text/markdown" }),
      text: async () => body,
    });
  }

  const sampleVersion: DocumentVersion = {
    version_id: 7,
    session_id: "sess-1",
    doc_type: "resume",
    version_counter: 2,
    generation_method: "template",
    use_counter: 0,
    created_at: "2026-04-20T12:00:00Z",
  };

  it("listVersions hits /api/documents/versions with session_id and token", async () => {
    mockJson([sampleVersion]);
    const { listVersions } = await import("../documents");
    const result = await listVersions("sess-1", "tkn");
    expect(result).toEqual([sampleVersion]);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/documents\/versions\?session_id=sess-1&token=tkn$/);
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
  });

  it("generateResume POSTs to /api/documents/resume with optional job_description", async () => {
    mockJson({
      version_id: 10,
      version_counter: 3,
      session_id: "sess-1",
      doc_type: "resume",
      generation_method: "template",
    });
    const { generateResume } = await import("../documents");
    await generateResume(
      { session_id: "sess-1", job_description: "Warehouse role" },
      "tkn",
    );
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/documents\/resume\?token=tkn$/);
    expect((init as RequestInit).method).toBe("POST");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      session_id: "sess-1",
      job_description: "Warehouse role",
    });
  });

  it("generateResume POSTs without job_description when omitted", async () => {
    mockJson({
      version_id: 11,
      version_counter: 1,
      session_id: "sess-1",
      doc_type: "resume",
      generation_method: "template",
    });
    const { generateResume } = await import("../documents");
    await generateResume({ session_id: "sess-1" }, "tkn");
    const [, init] = fetchMock.mock.calls[0];
    const body = JSON.parse((init as RequestInit).body as string);
    expect(body).toEqual({ session_id: "sess-1" });
  });

  it("getResumeMarkdown GETs /api/documents/resume/{id} as text", async () => {
    mockText("# hello");
    const { getResumeMarkdown } = await import("../documents");
    const md = await getResumeMarkdown(7, "tkn");
    expect(md).toBe("# hello");
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/documents\/resume\/7\?token=tkn$/);
  });

  it("resumePdfUrl returns the PDF download URL with the token", async () => {
    const { resumePdfUrl } = await import("../documents");
    const url = resumePdfUrl(7, "tkn");
    expect(url).toMatch(/\/api\/documents\/resume\/7\/pdf\?token=tkn$/);
  });

  it("generateCoverLetter POSTs with resume_version_id + job_match_ref", async () => {
    mockJson({
      version_id: 20,
      version_counter: 1,
      session_id: "sess-1",
      doc_type: "cover_letter",
      generation_method: "template",
      fair_chance: false,
    });
    const { generateCoverLetter } = await import("../documents");
    await generateCoverLetter(
      {
        session_id: "sess-1",
        resume_version_id: 7,
        job_match_ref: { job_id: "job-1", title: "Stocker", company: "Acme" },
      },
      "tkn",
    );
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/documents\/cover-letter\?token=tkn$/);
    expect((init as RequestInit).method).toBe("POST");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      session_id: "sess-1",
      resume_version_id: 7,
      job_match_ref: { job_id: "job-1", title: "Stocker", company: "Acme" },
    });
  });

  it("getCoverLetterMarkdown GETs cover-letter markdown", async () => {
    mockText("Dear hiring team,");
    const { getCoverLetterMarkdown } = await import("../documents");
    const md = await getCoverLetterMarkdown(20, "tkn");
    expect(md).toBe("Dear hiring team,");
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/documents\/cover-letter\/20\?token=tkn$/);
  });

  it("coverLetterPdfUrl returns the PDF URL", async () => {
    const { coverLetterPdfUrl } = await import("../documents");
    const url = coverLetterPdfUrl(20, "tkn");
    expect(url).toMatch(/\/api\/documents\/cover-letter\/20\/pdf\?token=tkn$/);
  });

  it("throws on non-ok JSON response with detail", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "bad token" }),
    });
    const { listVersions } = await import("../documents");
    await expect(listVersions("sess-1", "bad")).rejects.toThrow(/bad token/);
  });
});
