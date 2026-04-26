import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import type { Appointment } from "../appointments";

describe("appointments API client", () => {
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

  const sample: Appointment = {
    id: 1,
    session_id: "sess-1",
    type: "interview",
    title: "Interview at Acme",
    starts_at: "2026-05-01T15:00:00Z",
    ends_at: "2026-05-01T16:00:00Z",
    location_name: "Acme HQ",
    location_address: "123 Main St",
    barrier_link: null,
    status: "scheduled",
    source: "user",
    notes: null,
  };

  it("listAppointments hits GET /api/appointments with session and token", async () => {
    mockJson([sample]);
    const { listAppointments } = await import("../appointments");
    const result = await listAppointments("sess-1", "tkn");
    expect(result).toEqual([sample]);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/appointments\?session_id=sess-1&token=tkn$/);
    expect((init as RequestInit | undefined)?.method ?? "GET").toBe("GET");
  });

  it("listUpcoming hits /api/appointments/upcoming with days", async () => {
    mockJson([sample]);
    const { listUpcoming } = await import("../appointments");
    await listUpcoming("sess-1", 30, "tkn");
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(
      /\/api\/appointments\/upcoming\?session_id=sess-1&days=30&token=tkn$/,
    );
  });

  it("createAppointment POSTs with body", async () => {
    mockJson(sample);
    const { createAppointment } = await import("../appointments");
    await createAppointment(
      { session_id: "sess-1", type: "interview", title: "Interview" },
      "tkn",
    );
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/appointments\?token=tkn$/);
    expect((init as RequestInit).method).toBe("POST");
    expect(JSON.parse((init as RequestInit).body as string)).toMatchObject({
      session_id: "sess-1",
      type: "interview",
      title: "Interview",
    });
  });

  it("updateAppointment PATCHes with changes", async () => {
    mockJson(sample);
    const { updateAppointment } = await import("../appointments");
    await updateAppointment(1, { title: "Updated" }, "tkn");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/appointments\/1\?token=tkn$/);
    expect((init as RequestInit).method).toBe("PATCH");
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      title: "Updated",
    });
  });

  it("markAttended posts to /{id}/attended", async () => {
    mockJson({ ...sample, status: "attended" });
    const { markAttended } = await import("../appointments");
    const r = await markAttended(1, "tkn");
    expect(r.status).toBe("attended");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/appointments\/1\/attended\?token=tkn$/);
    expect((init as RequestInit).method).toBe("POST");
  });

  it("markMissed posts to /{id}/missed", async () => {
    mockJson({ ...sample, status: "missed" });
    const { markMissed } = await import("../appointments");
    await markMissed(1, "tkn");
    const [url] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/appointments\/1\/missed\?token=tkn$/);
  });

  it("cancelAppointment DELETEs", async () => {
    mockJson({ ...sample, status: "cancelled" });
    const { cancelAppointment } = await import("../appointments");
    await cancelAppointment(1, "tkn");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/appointments\/1\?token=tkn$/);
    expect((init as RequestInit).method).toBe("DELETE");
  });

  it("fromPathway posts to /api/appointments/from-pathway", async () => {
    mockJson([sample]);
    const { fromPathway } = await import("../appointments");
    await fromPathway("sess-1", "tkn");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(
      /\/api\/appointments\/from-pathway\?session_id=sess-1&token=tkn$/,
    );
    expect((init as RequestInit).method).toBe("POST");
  });

  it("throws on non-ok response with detail", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({ detail: "invalid session" }),
    });
    const { listAppointments } = await import("../appointments");
    await expect(listAppointments("bad", "tkn")).rejects.toThrow(
      /invalid session/,
    );
  });

  it(
    "still aborts via local timeout even when caller supplies their own signal (T13 stage-2 P1-4)",
    async () => {
      // Regression for the timeout-shadowing bug: previously the code
      // used ``init?.signal ?? controller.signal`` which dropped the
      // local timeout whenever the caller passed a signal. We now
      // compose both via ``AbortSignal.any``, so the local timeout
      // must still fire even with a caller signal in play.
      vi.useFakeTimers();
      try {
        // fetch resolves only when the signal it received aborts.
        let observedSignal: AbortSignal | undefined;
        fetchMock.mockImplementationOnce(
          (_url: string, init: RequestInit) => {
            observedSignal = init.signal as AbortSignal | undefined;
            return new Promise((_resolve, reject) => {
              observedSignal?.addEventListener("abort", () => {
                reject(
                  Object.assign(new Error("aborted"), { name: "AbortError" }),
                );
              });
            });
          },
        );

        const callerController = new AbortController();
        const { createAppointment } = await import("../appointments");
        const promise = createAppointment(
          { session_id: "s", type: "t", title: "x" },
          "tkn",
          // @ts-expect-error — caller-supplied signal not in the
          // public type but accepted by the underlying ``apiFetch``.
          { signal: callerController.signal },
        );
        // Tell vitest to ignore the unhandled rejection that surfaces
        // when fake-timers fire the timeout abort.
        promise.catch(() => undefined);

        // Advance past the 30s hard timeout. If the caller signal had
        // shadowed the local one, this would NOT trigger an abort and
        // ``promise`` would hang.
        await vi.advanceTimersByTimeAsync(31_000);

        await expect(promise).rejects.toMatchObject({ name: "AbortError" });
        expect(observedSignal).toBeDefined();
      } finally {
        vi.useRealTimers();
      }
    },
  );
});
