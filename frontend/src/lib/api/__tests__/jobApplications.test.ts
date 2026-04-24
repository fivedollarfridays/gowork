import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import type { JobApplication } from "../jobApplications";

describe("jobApplications API client", () => {
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

  const sample: JobApplication = {
    id: 1,
    session_id: "sess-1",
    match_source: "twc",
    match_url: "https://example.com/job/1",
    company: "Acme",
    role: "Janitor",
    resume_version_id: 42,
    status: "applied",
    applied_date: "2026-04-10",
    created_at: "2026-04-10T12:00:00Z",
  };

  it("listApplications GETs /api/job-applications with session and token", async () => {
    mockJson([sample]);
    const { listApplications } = await import("../jobApplications");
    const result = await listApplications("sess-1", "tkn");
    expect(result).toEqual([sample]);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(
      /\/api\/job-applications\?session_id=sess-1&token=tkn$/,
    );
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
  });

  it("updateApplicationStatus PATCHes with status in body", async () => {
    mockJson({ ...sample, status: "interview" });
    const { updateApplicationStatus } = await import("../jobApplications");
    await updateApplicationStatus(1, "interview", "tkn");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/job-applications\/1\?token=tkn$/);
    expect((init as RequestInit).method).toBe("PATCH");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      status: "interview",
    });
  });

  it("updateApplicationStatus includes outcome_date when provided", async () => {
    mockJson({ ...sample, status: "offer" });
    const { updateApplicationStatus } = await import("../jobApplications");
    await updateApplicationStatus(1, "offer", "tkn", "2026-04-15");
    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      status: "offer",
      outcome_date: "2026-04-15",
    });
  });

  it("getFunnel GETs /funnel and returns counts + rates", async () => {
    const funnel = {
      counts: {
        draft: 1,
        applied: 2,
        interview: 1,
        offer: 0,
        rejected: 0,
        withdrawn: 0,
      },
      draft_to_applied_rate: 0.75,
      applied_to_interview_rate: 0.5,
      interview_to_offer_rate: null,
    };
    mockJson(funnel);
    const { getFunnel } = await import("../jobApplications");
    const result = await getFunnel("sess-1", "tkn");
    expect(result).toEqual(funnel);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(
      /\/api\/job-applications\/funnel\?session_id=sess-1&token=tkn$/,
    );
  });

  it("listResumeVersions GETs /api/documents/versions", async () => {
    mockJson([
      {
        version_id: 42,
        session_id: "sess-1",
        doc_type: "resume",
        version_counter: 1,
        generation_method: "llm",
        use_counter: 3,
        created_at: "2026-04-10T12:00:00Z",
      },
    ]);
    const { listResumeVersions } = await import("../jobApplications");
    const result = await listResumeVersions("sess-1", "tkn");
    expect(result[0].generation_method).toBe("llm");
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(
      /\/api\/documents\/versions\?session_id=sess-1&token=tkn$/,
    );
  });

  it("throws on non-ok response with detail", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 409,
      statusText: "Conflict",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "invalid transition" }),
    });
    const { updateApplicationStatus } = await import("../jobApplications");
    await expect(
      updateApplicationStatus(1, "offer", "tkn"),
    ).rejects.toThrow(/invalid transition/);
  });
});
