/**
 * polish-2 T54 — FpsOverlayGate tests.
 *
 * Mounts the wall FpsOverlay only when:
 *   - process.env.NODE_ENV !== "production", AND
 *   - localStorage["gowork-fps"] === "1"
 *
 * In production: ALWAYS returns null (no overlay shipped to users).
 */
import React from "react";
import { describe, it, expect, afterEach, beforeEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";
import { FpsOverlayGate } from "../FpsOverlayGate";

beforeEach(() => {
  localStorage.clear();
  // Default test env is "test" (not production)
  vi.stubEnv("NODE_ENV", "test");
});

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.unstubAllEnvs();
});

describe("FpsOverlayGate (polish-2 T54)", () => {
  it("renders null when localStorage flag is unset", () => {
    const { container } = render(<FpsOverlayGate />);
    expect(container.querySelector("[data-fps-overlay]")).toBeNull();
  });

  it("renders the overlay when NODE_ENV != production AND gowork-fps=1", () => {
    localStorage.setItem("gowork-fps", "1");
    const { container } = render(<FpsOverlayGate />);
    expect(container.querySelector("[data-fps-overlay]")).not.toBeNull();
  });

  it("renders null in production even when the localStorage flag is set", () => {
    vi.stubEnv("NODE_ENV", "production");
    localStorage.setItem("gowork-fps", "1");
    const { container } = render(<FpsOverlayGate />);
    expect(container.querySelector("[data-fps-overlay]")).toBeNull();
  });

  it("renders null in production even when the flag is unset (defense in depth)", () => {
    vi.stubEnv("NODE_ENV", "production");
    const { container } = render(<FpsOverlayGate />);
    expect(container.querySelector("[data-fps-overlay]")).toBeNull();
  });
});
