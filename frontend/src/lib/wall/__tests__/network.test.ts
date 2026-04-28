import { describe, it, expect, afterEach } from "vitest";
import { getNetworkProfile } from "../network";

describe("network profile (T1.99)", () => {
  const original = (navigator as unknown as { connection?: unknown }).connection;

  afterEach(() => {
    if (original === undefined) {
      delete (navigator as unknown as { connection?: unknown }).connection;
    } else {
      (navigator as unknown as { connection?: unknown }).connection = original;
    }
  });

  it("reports the navigator.connection values when present", () => {
    Object.defineProperty(navigator, "connection", {
      value: { saveData: true, effectiveType: "3g", downlink: 1.5 },
      configurable: true,
    });
    const profile = getNetworkProfile();
    expect(profile.saveData).toBe(true);
    expect(profile.effectiveType).toBe("3g");
    expect(profile.downlinkMbps).toBe(1.5);
  });

  it("degrades gracefully when navigator.connection is undefined", () => {
    delete (navigator as unknown as { connection?: unknown }).connection;
    const profile = getNetworkProfile();
    expect(profile.saveData).toBe(false);
    expect(profile.effectiveType).toBe("unknown");
    expect(profile.downlinkMbps).toBeNull();
  });

  it("normalizes unknown effectiveType strings to 'unknown'", () => {
    Object.defineProperty(navigator, "connection", {
      value: { saveData: false, effectiveType: "5g-flying-car", downlink: 100 },
      configurable: true,
    });
    expect(getNetworkProfile().effectiveType).toBe("unknown");
  });
});
