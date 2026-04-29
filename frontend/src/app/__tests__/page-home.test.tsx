/**
 * app/page.tsx — sprint/gowork-facelift Driver D (Phase D3).
 *
 * The home page is now a thin shell:
 *   - Returning users (with a completed assessment in sessionStorage)
 *     are redirected to /daily.
 *   - First-time visitors get the 8-chapter `<HomePage>` shell.
 *
 * Locks the contract:
 *   - assessmentComplete=false → HomePage renders
 *   - assessmentComplete=true  → router.replace("/daily") fires
 */
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";

const replaceMock = vi.fn();
const assessmentCompleteMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("../home-redirect", () => ({
  useAssessmentComplete: () => assessmentCompleteMock(),
}));

vi.mock("@/components/home/HomePage", () => ({
  default: () =>
    React.createElement("div", { "data-testid": "home-page-stub" }, "HOME"),
}));

beforeEach(() => {
  replaceMock.mockReset();
  assessmentCompleteMock.mockReset();
});

afterEach(() => {
  cleanup();
});

describe("app/page.tsx — first-time visitors", () => {
  it("mounts <HomePage> when assessment NOT complete", async () => {
    assessmentCompleteMock.mockReturnValue(false);
    const { default: Home } = await import("../page");
    const { getByTestId } = render(React.createElement(Home));
    expect(getByTestId("home-page-stub")).toBeInTheDocument();
  });

  it("does NOT redirect when assessment NOT complete", async () => {
    assessmentCompleteMock.mockReturnValue(false);
    const { default: Home } = await import("../page");
    render(React.createElement(Home));
    expect(replaceMock).not.toHaveBeenCalled();
  });
});

describe("app/page.tsx — returning users", () => {
  it("redirects returning users to /daily via router.replace", async () => {
    assessmentCompleteMock.mockReturnValue(true);
    const { default: Home } = await import("../page");
    render(React.createElement(Home));
    expect(replaceMock).toHaveBeenCalledWith("/daily");
  });
});
