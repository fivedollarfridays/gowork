import { describe, it, expect } from "vitest";
import {
  constantTimeStringEqual,
  isAccessAllowed,
} from "../access";

describe("isAccessAllowed (T13.8 prod gate)", () => {
  it("allows access in development regardless of header", () => {
    expect(
      isAccessAllowed({
        nodeEnv: "development",
        headerKey: null,
        adminKey: undefined,
      }),
    ).toBe(true);
  });

  it("allows access in test mode", () => {
    expect(
      isAccessAllowed({
        nodeEnv: "test",
        headerKey: null,
        adminKey: undefined,
      }),
    ).toBe(true);
  });

  it("denies prod access when ADMIN_KEY is unset (fail-closed)", () => {
    expect(
      isAccessAllowed({
        nodeEnv: "production",
        headerKey: "anything",
        adminKey: undefined,
      }),
    ).toBe(false);
  });

  it("denies prod access when header doesn't match", () => {
    expect(
      isAccessAllowed({
        nodeEnv: "production",
        headerKey: "wrong-key",
        adminKey: "real-key",
      }),
    ).toBe(false);
  });

  it("allows prod access when header matches the configured admin key", () => {
    expect(
      isAccessAllowed({
        nodeEnv: "production",
        headerKey: "real-key",
        adminKey: "real-key",
      }),
    ).toBe(true);
  });

  it("denies prod access when header is null but admin key is set", () => {
    expect(
      isAccessAllowed({
        nodeEnv: "production",
        headerKey: null,
        adminKey: "real-key",
      }),
    ).toBe(false);
  });
});

describe("constantTimeStringEqual (T13 stage-2 P1-3)", () => {
  it("returns true for equal strings", () => {
    expect(constantTimeStringEqual("abc123", "abc123")).toBe(true);
  });

  it("returns false for different-length strings without throwing", () => {
    // The early length-check is required: ``timingSafeEqual`` itself
    // throws RangeError on unequal-length inputs.
    expect(constantTimeStringEqual("abc", "abc1")).toBe(false);
    expect(constantTimeStringEqual("", "x")).toBe(false);
  });

  it("returns false for same-length but differing strings", () => {
    expect(constantTimeStringEqual("abc", "abd")).toBe(false);
    // First-byte mismatch — the prior `===` impl leaked timing here.
    expect(constantTimeStringEqual("aaaa", "baaa")).toBe(false);
  });

  it("returns true for two empty strings", () => {
    // Empty admin keys are rejected upstream, but the helper must be
    // total: equal-length zero-byte buffers should compare equal.
    expect(constantTimeStringEqual("", "")).toBe(true);
  });
});
