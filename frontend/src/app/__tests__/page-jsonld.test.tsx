/**
 * polish-2 T51 — page.tsx JSON-LD inline test.
 *
 * Verifies the home route emits a `<script type="application/ld+json">`
 * tag containing the WebSite + BreadcrumbList structured-data payload
 * (and an Article entry when `?chapter=N` is supplied).
 */
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("../home-redirect", () => ({
  useAssessmentComplete: () => false,
}));

vi.mock("@/components/home/HomePage", () => ({
  default: () =>
    React.createElement("div", { "data-testid": "home-page-stub" }, "HOME"),
}));

afterEach(() => cleanup());
beforeEach(() => undefined);

async function renderPage(chapter?: string) {
  const { default: Home } = await import("../page");
  // Server component returns a Promise<JSX.Element>
  const tree = await Home({
    searchParams: Promise.resolve(
      chapter !== undefined ? { chapter } : {},
    ),
  } as Parameters<typeof Home>[0]);
  return render(tree as React.ReactElement);
}

describe("app/page.tsx JSON-LD (polish-2 T51)", () => {
  it("emits a <script type='application/ld+json'> tag", async () => {
    const { container } = await renderPage();
    const script = container.querySelector(
      "script[type='application/ld+json']",
    );
    expect(script).not.toBeNull();
  });

  it("the script contains a WebSite entry", async () => {
    const { container } = await renderPage();
    const script = container.querySelector(
      "script[type='application/ld+json']",
    );
    const txt = script?.textContent ?? "";
    expect(txt).toContain('"@type":"WebSite"');
  });

  it("the script contains an Article entry when ?chapter=3", async () => {
    const { container } = await renderPage("3");
    const script = container.querySelector(
      "script[type='application/ld+json']",
    );
    const txt = script?.textContent ?? "";
    expect(txt).toContain('"@type":"Article"');
    expect(txt).toMatch(/Carlos/i);
  });

  it("renders the HomePage stub (page composition still works)", async () => {
    const { getByTestId } = await renderPage();
    expect(getByTestId("home-page-stub")).toBeInTheDocument();
  });
});
