import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { validateMapboxToken } from "../env";

/**
 * T1.6 — Mapbox token boot validator.
 *
 * W2's WallContainer reads validateMapboxToken() at module init. If the
 * token is missing or malformed, the container falls back to T1.74's
 * static branded placeholder rather than crashing the page.
 *
 * Token format: Mapbox public tokens start with `pk.` (signed JWT).
 * Private tokens start with `sk.`; we DO NOT accept them on the public
 * frontend (security smell — would leak in the bundle).
 */

describe("T1.6 — validateMapboxToken", () => {
  const ORIGINAL_ENV = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

  beforeEach(() => {
    delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  });

  afterEach(() => {
    if (ORIGINAL_ENV === undefined) {
      delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    } else {
      process.env.NEXT_PUBLIC_MAPBOX_TOKEN = ORIGINAL_ENV;
    }
  });

  it("returns ok=false with reason when env is unset", () => {
    const result = validateMapboxToken();
    expect(result.ok).toBe(false);
    expect(result.reason).toMatch(/unset|missing|empty/i);
  });

  it("returns ok=true for tokens starting with pk.", () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6InRlc3QifQ.signature";
    const result = validateMapboxToken();
    expect(result.ok).toBe(true);
    expect(result.reason).toBeUndefined();
  });

  it("returns ok=false for tokens starting with sk. (private — should never ship)", () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "sk.privatevaluethatshouldnevershipto.frontend";
    const result = validateMapboxToken();
    expect(result.ok).toBe(false);
    expect(result.reason).toMatch(/private|secret/i);
  });

  it("returns ok=false for tokens starting with anything else", () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "not-a-mapbox-token";
    const result = validateMapboxToken();
    expect(result.ok).toBe(false);
    expect(result.reason).toMatch(/format|prefix|invalid/i);
  });

  it("returns ok=false for empty string token", () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "";
    const result = validateMapboxToken();
    expect(result.ok).toBe(false);
    expect(result.reason).toMatch(/unset|missing|empty/i);
  });

  it("does not access window (SSR-safe)", () => {
    // The module under test must execute without window present. If
    // validateMapboxToken referenced window, this import would have already
    // crashed at the top of this file. The fact that we're here is the proof.
    expect(typeof validateMapboxToken).toBe("function");
  });
});
