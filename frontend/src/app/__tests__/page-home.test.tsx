/**
 * app/page.tsx — sprint/gowork-facelift Driver D (Phase D3).
 * polish-2 T51 — page.tsx is now a server component; the redirect logic
 * lives in `app/page-client.tsx`.
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

describe("app/page-client.tsx — first-time visitors", () => {
  it("mounts <HomePage> when assessment NOT complete", async () => {
    assessmentCompleteMock.mockReturnValue(false);
    const { default: HomeClient } = await import("../page-client");
    const { getByTestId } = render(React.createElement(HomeClient));
    expect(getByTestId("home-page-stub")).toBeInTheDocument();
  });

  it("does NOT redirect when assessment NOT complete", async () => {
    assessmentCompleteMock.mockReturnValue(false);
    const { default: HomeClient } = await import("../page-client");
    render(React.createElement(HomeClient));
    expect(replaceMock).not.toHaveBeenCalled();
  });
});

describe("app/page-client.tsx — returning users", () => {
  it("redirects returning users to /daily via router.replace", async () => {
    assessmentCompleteMock.mockReturnValue(true);
    const { default: HomeClient } = await import("../page-client");
    render(React.createElement(HomeClient));
    expect(replaceMock).toHaveBeenCalledWith("/daily");
  });
});
