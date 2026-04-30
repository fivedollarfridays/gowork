import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

/**
 * T2.46 — Archive existing landing.
 *
 * The pre-Wall landing page is preserved at `frontend/src/app/archive/page.tsx`
 * so we can roll back to "before The Wall" via a one-line page.tsx swap.
 * This is rollback insurance for demo day, not a discoverable route — it
 * isn't linked from the footer.
 *
 * Tests:
 *   - /archive renders without throwing
 *   - /archive contains the legacy hero question (locked W1 copy)
 *   - /archive renders flow steps
 */

// Stub the redirect hook (the archive shouldn't redirect at all).
vi.mock("../../home-redirect", () => ({
  useAssessmentComplete: () => false,
}));

// Next.js router stub — the archive page calls `useRouter().replace`
// inside an effect, but the test only renders one frame.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/archive",
  useSearchParams: () => new URLSearchParams(),
}));

// Stub useCityConfig (T1 hook — returns FW config in tests).
vi.mock("@/hooks/useCityConfig", () => ({
  useCityConfig: () => ({
    state: "TX",
    cityName: "Fort Worth",
    population: 956709,
  }),
}));

// Stub i18n so we don't depend on file-system translations in this test.
vi.mock("@/lib/i18n", () => ({
  t: (key: string) => key,
}));

// framer-motion lazy-loaded child wrappers.
vi.mock("@/lib/motion", () => ({
  ScrollReveal: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
  StaggerContainer: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
  StaggerItem: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
  Typewriter: ({ text }: { text: string }) =>
    React.createElement("span", null, text),
  AnimatedCounter: ({ to, suffix }: { to: number; suffix?: string }) =>
    React.createElement("span", null, `${to}${suffix ?? ""}`),
}));

afterEach(() => {
  cleanup();
});

describe("T2.46 — /archive renders the pre-Wall landing", () => {
  it("renders the legacy hero question key (i18n) without throwing", async () => {
    const { default: ArchivedHome } = await import("../archive/page");
    const { container } = render(React.createElement(ArchivedHome));
    expect(container.textContent).toContain("home.heroQuestion");
  });

  it("renders the legacy 3-step flow (Assess / Match / Plan)", async () => {
    const { default: ArchivedHome } = await import("../archive/page");
    const { container } = render(React.createElement(ArchivedHome));
    expect(container.textContent).toContain("home.stepAssessTitle");
    expect(container.textContent).toContain("home.stepMatchTitle");
    expect(container.textContent).toContain("home.stepPlanTitle");
  });
});
