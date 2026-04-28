/**
 * FpsOverlay (T1.82) — dev-only rolling FPS readout.
 *
 * Hidden in production, behind reduced-motion, and unless either
 * `?fps=1` is in the URL or `window.__GOWORK_FPS__` is true.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render } from "@testing-library/react";

function setSearch(search: string): void {
  Object.defineProperty(window, "location", {
    configurable: true,
    value: { ...window.location, search },
  });
}

describe("FpsOverlay (T1.82)", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    vi.stubEnv("NODE_ENV", "development");
    setSearch("");
    delete (window as unknown as { __GOWORK_FPS__?: boolean }).__GOWORK_FPS__;
  });
  afterEach(() => {
    setSearch("");
    vi.unstubAllEnvs();
  });

  it("renders nothing in production regardless of toggles", async () => {
    vi.stubEnv("NODE_ENV", "production");
    setSearch("?fps=1");
    vi.resetModules();
    const { FpsOverlay } = await import("../FpsOverlay");
    const { container } = render(<FpsOverlay />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing without ?fps=1 nor window.__GOWORK_FPS__", async () => {
    vi.resetModules();
    const { FpsOverlay } = await import("../FpsOverlay");
    const { container } = render(<FpsOverlay />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the overlay when ?fps=1 is in the URL", async () => {
    setSearch("?fps=1");
    vi.resetModules();
    const { FpsOverlay } = await import("../FpsOverlay");
    const { container } = render(<FpsOverlay />);
    expect(container.querySelector("[data-testid='fps-overlay']")).toBeTruthy();
  });

  it("renders the overlay when window.__GOWORK_FPS__ is true", async () => {
    (window as unknown as { __GOWORK_FPS__?: boolean }).__GOWORK_FPS__ = true;
    vi.resetModules();
    const { FpsOverlay } = await import("../FpsOverlay");
    const { container } = render(<FpsOverlay />);
    expect(container.querySelector("[data-testid='fps-overlay']")).toBeTruthy();
  });
});
