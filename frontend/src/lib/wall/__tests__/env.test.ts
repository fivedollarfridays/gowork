import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

describe("validateMapboxToken (T1.6)", () => {
  const ORIGINAL_ENV = { ...process.env };

  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it("returns ok=false when NEXT_PUBLIC_MAPBOX_TOKEN is unset", async () => {
    delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    const { validateMapboxToken } = await import("../env");
    const result = validateMapboxToken();
    expect(result.ok).toBe(false);
    expect(result.reason).toBeDefined();
  });

  it("returns ok=false when token is empty string", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "";
    const { validateMapboxToken } = await import("../env");
    const result = validateMapboxToken();
    expect(result.ok).toBe(false);
  });

  it("returns ok=true when token starts with pk.", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoidGVzdCIsImEiOiJjazAwMDAwMCJ9.fake";
    const { validateMapboxToken } = await import("../env");
    const result = validateMapboxToken();
    expect(result.ok).toBe(true);
    expect(result.reason).toBeUndefined();
  });

  it("returns ok=false when token does not start with pk.", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "sk.invalid_secret_token";
    const { validateMapboxToken } = await import("../env");
    const result = validateMapboxToken();
    expect(result.ok).toBe(false);
    expect(result.reason).toMatch(/pk\./i);
  });

  it("isMapboxAvailable mirrors validateMapboxToken().ok", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.real_token";
    const { isMapboxAvailable, validateMapboxToken } = await import("../env");
    expect(isMapboxAvailable()).toBe(validateMapboxToken().ok);
  });

  it("getMapboxToken returns the raw token string when ok", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.token_value";
    const { getMapboxToken } = await import("../env");
    expect(getMapboxToken()).toBe("pk.token_value");
  });

  it("getMapboxToken returns null when token absent", async () => {
    delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    const { getMapboxToken } = await import("../env");
    expect(getMapboxToken()).toBeNull();
  });
});
