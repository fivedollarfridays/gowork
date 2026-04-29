/**
 * ChromeFrame — sprint/gowork-facelift Driver D.
 *
 * Wrapper for the canonical app-chrome (Header + Footer) that renders
 * children for every route EXCEPT the home route `/`. The home route
 * mounts its own dedicated `<SiteHeader>` + `<SiteFooter>` (Driver A's
 * scrollytelling chrome) so the canonical app chrome must not double up.
 *
 * Contract:
 *   - usePathname() === "/"          → returns null (children NOT rendered)
 *   - usePathname() === "/daily"     → renders children
 *   - usePathname() === "/jobs"      → renders children
 *   - usePathname() === "/case-manager" → renders children
 *   - usePathname() === null         → renders children (SSR-safe default)
 */
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, cleanup, screen } from "@testing-library/react";

const pathnameMock = vi.fn();
vi.mock("next/navigation", () => ({
  usePathname: () => pathnameMock(),
}));

beforeEach(() => {
  pathnameMock.mockReset();
});

afterEach(() => {
  cleanup();
});

describe("ChromeFrame — skip on home route", () => {
  it("renders nothing when pathname is '/'", async () => {
    pathnameMock.mockReturnValue("/");
    const { ChromeFrame } = await import("../ChromeFrame");
    const { container } = render(
      <ChromeFrame>
        <div data-testid="chrome-child">CHROME</div>
      </ChromeFrame>,
    );
    expect(container.querySelector('[data-testid="chrome-child"]')).toBeNull();
  });

  it("renders children when pathname is '/daily'", async () => {
    pathnameMock.mockReturnValue("/daily");
    const { ChromeFrame } = await import("../ChromeFrame");
    render(
      <ChromeFrame>
        <div data-testid="chrome-child">CHROME</div>
      </ChromeFrame>,
    );
    expect(screen.getByTestId("chrome-child")).toBeInTheDocument();
  });

  it("renders children when pathname is '/jobs'", async () => {
    pathnameMock.mockReturnValue("/jobs");
    const { ChromeFrame } = await import("../ChromeFrame");
    render(
      <ChromeFrame>
        <div data-testid="chrome-child">CHROME</div>
      </ChromeFrame>,
    );
    expect(screen.getByTestId("chrome-child")).toBeInTheDocument();
  });

  it("renders children when pathname is '/case-manager'", async () => {
    pathnameMock.mockReturnValue("/case-manager");
    const { ChromeFrame } = await import("../ChromeFrame");
    render(
      <ChromeFrame>
        <div data-testid="chrome-child">CHROME</div>
      </ChromeFrame>,
    );
    expect(screen.getByTestId("chrome-child")).toBeInTheDocument();
  });

  it("renders children when pathname is null (SSR-safe default)", async () => {
    pathnameMock.mockReturnValue(null);
    const { ChromeFrame } = await import("../ChromeFrame");
    render(
      <ChromeFrame>
        <div data-testid="chrome-child">CHROME</div>
      </ChromeFrame>,
    );
    expect(screen.getByTestId("chrome-child")).toBeInTheDocument();
  });
});
