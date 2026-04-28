import { describe, it, expect } from "vitest";

describe("hooks barrel (T1.69)", () => {
  it("re-exports the 10 W1 utility hooks", async () => {
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
  });

  it("re-exports the legacy hooks", async () => {
    const mod = await import("../index");
    expect(typeof mod.useTranslation).toBe("function");
    expect(typeof mod.useCityConfig).toBe("function");
  });

  it("re-exports localStorage key constants for migration", async () => {
    const mod = await import("../index");
    expect(mod.GOWORK_LOCALE_KEY).toBe("gowork.locale");
    expect(mod.LEGACY_LOCALE_KEY).toBe("montgowork-locale");
  });
});
