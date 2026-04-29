/**
 * typewriter.ts unit tests — polish-2 Driver B (T19).
 *
 * The typewriter helper resolves the full string when finished. Under
 * `instant: true` it skips the animation and resolves immediately. Each
 * `onTick` callback fires once per character with the cumulative
 * substring. AbortSignal aborts cleanly without resolving.
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { typewrite } from "../typewriter";

afterEach(() => {
  vi.useRealTimers();
});

describe("typewrite — instant path", () => {
  it("resolves immediately with the full text when instant=true", async () => {
    const result = await typewrite("Hello", { instant: true });
    expect(result).toBe("Hello");
  });

  it("calls onTick once with the full string under instant=true", async () => {
    const ticks: string[] = [];
    await typewrite("ABC", {
      instant: true,
      onTick: (s) => {
        ticks.push(s);
      },
    });
    expect(ticks).toEqual(["ABC"]);
  });
});

describe("typewrite — animated path", () => {
  it("emits one onTick per character in order", async () => {
    vi.useFakeTimers();
    const ticks: string[] = [];
    const promise = typewrite("hi", {
      charDelay: 10,
      onTick: (s) => {
        ticks.push(s);
      },
    });
    await vi.advanceTimersByTimeAsync(50);
    await promise;
    expect(ticks).toEqual(["h", "hi"]);
  });

  it("resolves with the full text after the animated reveal completes", async () => {
    vi.useFakeTimers();
    const promise = typewrite("abcd", { charDelay: 5 });
    await vi.advanceTimersByTimeAsync(50);
    const result = await promise;
    expect(result).toBe("abcd");
  });

  it("defaults to ~55ms charDelay (≈18 char/sec)", async () => {
    vi.useFakeTimers();
    const ticks: string[] = [];
    const promise = typewrite("ab", {
      onTick: (s) => {
        ticks.push(s);
      },
    });
    // 1 character at 55ms — should emit "a" but not "ab" yet.
    await vi.advanceTimersByTimeAsync(60);
    expect(ticks).toEqual(["a"]);
    await vi.advanceTimersByTimeAsync(60);
    await promise;
    expect(ticks).toEqual(["a", "ab"]);
  });
});

describe("typewrite — abort signal", () => {
  it("aborts cleanly mid-reveal without rejecting", async () => {
    vi.useFakeTimers();
    const ctl = new AbortController();
    const ticks: string[] = [];
    const promise = typewrite(
      "abcdef",
      {
        charDelay: 10,
        onTick: (s) => {
          ticks.push(s);
        },
      },
      ctl.signal,
    );
    await vi.advanceTimersByTimeAsync(15);
    ctl.abort();
    await vi.advanceTimersByTimeAsync(200);
    const result = await promise;
    // Aborted reveal returns whatever was emitted so far (or "").
    expect(result.length).toBeLessThan(6);
  });

  it("does not call onTick after abort", async () => {
    vi.useFakeTimers();
    const ctl = new AbortController();
    const ticks: string[] = [];
    const promise = typewrite(
      "abcdef",
      {
        charDelay: 10,
        onTick: (s) => {
          ticks.push(s);
        },
      },
      ctl.signal,
    );
    await vi.advanceTimersByTimeAsync(12);
    ctl.abort();
    const beforeAbortLen = ticks.length;
    await vi.advanceTimersByTimeAsync(200);
    await promise;
    expect(ticks.length).toBe(beforeAbortLen);
  });

  it("if signal is already aborted, resolves immediately with empty progress", async () => {
    const ctl = new AbortController();
    ctl.abort();
    const ticks: string[] = [];
    const result = await typewrite(
      "abc",
      { charDelay: 10, onTick: (s) => ticks.push(s) },
      ctl.signal,
    );
    expect(result).toBe("");
    expect(ticks).toEqual([]);
  });
});
