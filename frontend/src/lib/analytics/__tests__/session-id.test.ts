import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { getSessionId, _resetSessionForTests, SESSION_STORAGE_KEY } from "../session-id";

describe("RUM session id (T1.81)", () => {
  beforeEach(() => {
    sessionStorage.clear();
    _resetSessionForTests();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns a 64-character hex string", async () => {
    const id = await getSessionId();
    expect(id).toMatch(/^[0-9a-f]{64}$/);
  });

  it("returns the same id within a tab session", async () => {
    const a = await getSessionId();
    const b = await getSessionId();
    expect(a).toBe(b);
  });

  it("regenerates after sessionStorage is cleared", async () => {
    const a = await getSessionId();
    sessionStorage.clear();
    _resetSessionForTests();
    const b = await getSessionId();
    expect(a).not.toBe(b);
  });

  it("does not store raw user-agent or screen size in sessionStorage", async () => {
    await getSessionId();
    const stored = sessionStorage.getItem(SESSION_STORAGE_KEY) ?? "";
    expect(stored).not.toContain(navigator.userAgent);
    expect(stored).toMatch(/^[0-9a-f]{64}$/);
  });

  it("falls back to a deterministic hash when crypto.subtle is unavailable", async () => {
    const original = (globalThis.crypto as unknown as { subtle?: unknown }).subtle;
    Object.defineProperty(globalThis.crypto, "subtle", { value: undefined, configurable: true });
    const id = await getSessionId();
    expect(id).toMatch(/^[0-9a-f]{64}$/);
    Object.defineProperty(globalThis.crypto, "subtle", { value: original, configurable: true });
  });

  it("returns 'ssr' when window is unavailable (server)", async () => {
    const originalWindow = globalThis.window;
    // @ts-expect-error - intentional SSR simulation
    delete globalThis.window;
    _resetSessionForTests();
    const id = await getSessionId();
    expect(id).toBe("ssr");
    globalThis.window = originalWindow;
  });
});
