import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

/**
 * T2.47 — frontend/src/app/page.tsx renders WallContainer.
 *
 * The new home page is a thin shell: redirect returning users to /daily
 * (preserving W1's `useAssessmentComplete` contract), otherwise mount
 * `<WallContainer>` for first-time visitors.
 *
 * This test locks the contract:
 *   - assessmentComplete=false → WallContainer renders
 *   - assessmentComplete=true → router.replace("/daily") fires
 *   - page is under 50 lines (verified separately by `arch check`)
 */

const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

const assessmentCompleteMock = vi.fn();
vi.mock("../home-redirect", () => ({
  useAssessmentComplete: () => assessmentCompleteMock(),
}));

// Stub WallContainer + chapter mounts so we can assert composition only.
vi.mock("@/components/wall/WallContainer", () => ({
  default: () =>
    React.createElement("div", { "data-testid": "wall-container-stub" }, "WALL"),
}));

beforeEach(() => {
  replaceMock.mockReset();
  assessmentCompleteMock.mockReset();
});

afterEach(() => {
  cleanup();
});

describe("T2.47 — page.tsx for first-time visitors", () => {
  it("mounts <WallContainer> when assessment NOT complete", async () => {
    assessmentCompleteMock.mockReturnValue(false);
    const { default: Home } = await import("../page");
    const { getByTestId } = render(React.createElement(Home));
    expect(getByTestId("wall-container-stub")).toBeInTheDocument();
  });

  it("does NOT redirect when assessment NOT complete", async () => {
    assessmentCompleteMock.mockReturnValue(false);
    const { default: Home } = await import("../page");
    render(React.createElement(Home));
    expect(replaceMock).not.toHaveBeenCalled();
  });
});

describe("T2.47 — page.tsx for returning users", () => {
  it("redirects returning users to /daily via router.replace", async () => {
    assessmentCompleteMock.mockReturnValue(true);
    const { default: Home } = await import("../page");
    render(React.createElement(Home));
    expect(replaceMock).toHaveBeenCalledWith("/daily");
  });
});
