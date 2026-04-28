import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { report, scrubContext, scrubStackTrace, _resetReporterForTests } from "../error-reporter";

describe("error reporter (T1.117)", () => {
  beforeEach(() => {
    _resetReporterForTests();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("scrubContext", () => {
    it("replaces email values with <EMAIL>", () => {
      const scrubbed = scrubContext({ user: "carlos@example.com", section: "chapter-4" });
      expect(scrubbed.user).toBe("<EMAIL>");
      expect(scrubbed.section).toBe("chapter-4");
    });

    it("preserves numeric values unchanged", () => {
      const scrubbed = scrubContext({ chapter: 4, retries: 0 });
      expect(scrubbed.chapter).toBe(4);
      expect(scrubbed.retries).toBe(0);
    });

    it("returns an empty object for undefined context", () => {
      expect(scrubContext(undefined)).toEqual({});
    });
  });

  describe("scrubStackTrace", () => {
    it("replaces /Users/<name> with <USER>", () => {
      const scrubbed = scrubStackTrace("at fn (/Users/carlos/work/file.ts:10:5)");
      expect(scrubbed).toContain("<USER>");
      expect(scrubbed).not.toContain("carlos");
    });

    it("replaces C:\\Users\\<name> with <USER>", () => {
      const scrubbed = scrubStackTrace("at fn (C:\\Users\\Carlos\\work\\file.ts:10:5)");
      expect(scrubbed).toContain("<USER>");
      expect(scrubbed).not.toContain("Carlos");
    });

    it("returns empty string for undefined stack", () => {
      expect(scrubStackTrace(undefined)).toBe("");
    });
  });

  describe("report", () => {
    it("calls console.error in dev with the scrubbed payload", () => {
      const spy = vi.spyOn(console, "error").mockImplementation(() => {});
      report(new Error("boom"), { user: "x@y.com", section: "c4" });
      expect(spy).toHaveBeenCalledTimes(1);
      const payload = spy.mock.calls[0][1] as Record<string, unknown>;
      const ctx = payload.context as Record<string, unknown>;
      expect(ctx.user).toBe("<EMAIL>");
      expect(ctx.section).toBe("c4");
    });

    it("swallows fetch failures (W4 endpoint not yet present)", async () => {
      const fetchSpy = vi.fn().mockRejectedValue(new Error("ECONN"));
      vi.stubGlobal("fetch", fetchSpy);
      vi.spyOn(console, "error").mockImplementation(() => {});
      expect(() => report(new Error("boom"))).not.toThrow();
      vi.unstubAllGlobals();
    });
  });
});
