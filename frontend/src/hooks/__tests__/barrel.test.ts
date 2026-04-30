import { describe, it, expect } from "vitest";

// W4 — barrel surface grew with hero font + sky setter + Live Now
// formatter + rAF throttler. Cold-cache imports under parallel load
// occasionally exceed the 5s default; widen to 15s.
const BARREL_IMPORT_TIMEOUT = 15_000;

describe("hooks barrel (T1.69)", () => {
  it(
    "re-exports the 10 W1 utility hooks",
    async () => {
      const mod = await import("../index");
      expect(typeof mod.useTimeOfDay).toBe("function");
      expect(typeof mod.useCursorPosition).toBe("function");
      expect(typeof mod.useLiveNow).toBe("function");
      expect(typeof mod.useScrollProgress).toBe("function");
      expect(typeof mod.useVariableFontWeight).toBe("function");
      expect(typeof mod.useScrollVelocity).toBe("function");
      expect(typeof mod.usePrefersReducedMotion).toBe("function");
      expect(typeof mod.useIdleState).toBe("function");
      expect(typeof mod.useViewTransitionsSupport).toBe("function");
      expect(typeof mod.useLanguage).toBe("function");
    },
    BARREL_IMPORT_TIMEOUT,
  );

  it(
    "re-exports the legacy hooks",
    async () => {
      const mod = await import("../index");
      expect(typeof mod.useTranslation).toBe("function");
      expect(typeof mod.useCityConfig).toBe("function");
    },
    BARREL_IMPORT_TIMEOUT,
  );

  it(
    "re-exports localStorage key constants for migration",
    async () => {
      const mod = await import("../index");
      expect(mod.GOWORK_LOCALE_KEY).toBe("gowork.locale");
      expect(mod.LEGACY_LOCALE_KEY).toBe("montgowork-locale");
    },
    BARREL_IMPORT_TIMEOUT,
  );

  it(
    "re-exports the W4 life-engine hooks (T4.A)",
    async () => {
      const mod = await import("../index");
      expect(typeof mod.useHeroFontWeight).toBe("function");
      expect(typeof mod.useChapterHeadingFontWeight).toBe("function");
      expect(typeof mod.useMapboxSkyForTimeOfDay).toBe("function");
      expect(typeof mod.useThrottledRAF).toBe("function");
      expect(typeof mod.useLiveNowFormatted).toBe("function");
    },
    BARREL_IMPORT_TIMEOUT,
  );
});
