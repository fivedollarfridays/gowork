import { describe, it, expect, beforeEach } from "vitest";

beforeEach(() => {
  // env.test sets process.env.NEXT_PUBLIC_MAPBOX_TOKEN; reset for predictability
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

describe("lib/wall barrel (T1.68)", () => {
  it("re-exports validateMapboxToken from env", async () => {
    const mod = await import("../index");
    expect(typeof mod.validateMapboxToken).toBe("function");
    expect(typeof mod.isMapboxAvailable).toBe("function");
    expect(typeof mod.getMapboxToken).toBe("function");
  });

  it("re-exports the sound module under the `sound` namespace", async () => {
    const mod = await import("../index");
    expect(typeof mod.sound.play).toBe("function");
    expect(typeof mod.sound.stop).toBe("function");
    expect(typeof mod.sound.setMuted).toBe("function");
    expect(typeof mod.sound.isMuted).toBe("function");
  });

  it("types re-exports compile (smoke check)", async () => {
    const mod = await import("../index");
    // Types are erased at runtime — this just asserts import resolves.
    expect(mod).toBeDefined();
  });
});
