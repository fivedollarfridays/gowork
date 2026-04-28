import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useLiveNow } from "../useLiveNow";

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  });
  return ({ children }: { children: ReactNode }) =>
    React.createElement(QueryClientProvider, { client }, children);
}

describe("useLiveNow (T1.26)", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("returns client-computed now and zero sessions when /api/now returns 404", async () => {
    (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 404,
    });
    const { result } = renderHook(() => useLiveNow(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.now).toBeInstanceOf(Date));
    expect(result.current.sessions).toBe(0);
    expect(result.current.lastCalibration).toBeNull();
  });

  it("returns server-supplied data when /api/now is healthy", async () => {
    (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          now: "2026-04-27T12:00:00.000Z",
          sessions: 42,
          lastCalibration: "2026-04-26T08:00:00.000Z",
        }),
    });
    const { result } = renderHook(() => useLiveNow(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.sessions).toBe(42));
    expect(result.current.lastCalibration).toBeInstanceOf(Date);
  });

  it("falls back gracefully when fetch rejects (network error)", async () => {
    (global.fetch as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(new Error("ECONN"));
    const { result } = renderHook(() => useLiveNow(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.now).toBeInstanceOf(Date));
    expect(result.current.sessions).toBe(0);
    expect(result.current.lastCalibration).toBeNull();
  });

  it("exposes a stable shape on first synchronous render (no undefined fields)", () => {
    (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 404,
    });
    const { result } = renderHook(() => useLiveNow(), { wrapper: makeWrapper() });
    expect(result.current.now).toBeDefined();
    expect(result.current.sessions).toBe(0);
    expect(result.current.lastCalibration).toBeNull();
  });
});
