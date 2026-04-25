import { describe, it, expect } from "vitest";
import { isAccessAllowed } from "../access";

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
