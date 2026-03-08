import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useBarrierIntelStream } from "@/hooks/useBarrierIntelStream";

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe("useBarrierIntelStream", () => {
  it("starts idle", () => {
    const { result } = renderHook(() => useBarrierIntelStream());
    expect(result.current.status).toBe("idle");
    expect(result.current.messages).toHaveLength(0);
  });

  it("sends question and collects streamed tokens", async () => {
    const tokenEvent = `data: ${JSON.stringify({ type: "token", text: "Hello!" })}\n\n`;
    const doneEvent = `data: ${JSON.stringify({ type: "done", usage: { input_tokens: 10, output_tokens: 5 } })}\n\n`;

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: makeStream([tokenEvent, doneEvent]),
    });

    const { result } = renderHook(() => useBarrierIntelStream());

    await act(async () => {
      await result.current.sendQuestion("session-1", "What to do?");
    });

    expect(result.current.status).toBe("done");
    expect(result.current.messages.length).toBeGreaterThanOrEqual(2);
    const assistantMsg = result.current.messages.find((m) => m.role === "assistant");
    expect(assistantMsg?.text).toContain("Hello!");
  });

  it("sets status to error on fetch failure", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useBarrierIntelStream());

    await act(async () => {
      await result.current.sendQuestion("session-1", "What to do?");
    });

    expect(result.current.status).toBe("error");
  });
});
