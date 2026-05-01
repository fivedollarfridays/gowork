/**
 * HomePage — sprint/gowork-facelift Driver D (Phase D3).
 *
 * Top-level shell for the 8-chapter scrollytelling homepage. Mounts in
 * this order:
 *   1. CursorFlashlight   — animated radial glow following the cursor
 *   2. SiteHeader         — sticky glass-blur top bar
 *   3. ChapterRail        — vertical chapter pager (xl+)
 *   4. PageMeta           — bottom-right TIME · CITY · CHAPTER · SCROLL
 *   5. <main>             — Chapter01..Chapter08 in order
 *   6. SiteFooter         — bottom links + tagline
 *
 * GSAP/ScrollTrigger-touching chapters are imported via next/dynamic
 * (`{ ssr: false }`) so the SSR pass doesn't try to register Lenis or
 * GSAP plugins on the server.
 */
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";

// Stub out the Driver A/B chapter components — we only assert composition.
vi.mock("@/components/home/SiteHeader", () => ({
  SiteHeader: () =>
    React.createElement("div", { "data-testid": "stub-site-header" }, "HEADER"),
}));
vi.mock("@/components/home/SiteFooter", () => ({
  SiteFooter: () =>
    React.createElement("div", { "data-testid": "stub-site-footer" }, "FOOTER"),
}));
vi.mock("@/components/home/ChapterRail", () => ({
  ChapterRail: () =>
    React.createElement("div", { "data-testid": "stub-chapter-rail" }, "RAIL"),
}));
vi.mock("@/components/home/PageMeta", () => ({
  PageMeta: () =>
    React.createElement("div", { "data-testid": "stub-page-meta" }, "META"),
}));
vi.mock("@/components/home/CursorFlashlight", () => ({
  CursorFlashlight: () =>
    React.createElement(
      "div",
      { "data-testid": "stub-cursor-flashlight" },
      "FLASHLIGHT",
    ),
}));

// next/dynamic — return a stub component for any dynamic-imported chapter.
vi.mock("next/dynamic", () => ({
  default: (loader: () => Promise<unknown>, _opts?: unknown) => {
    // The loader path argument leaks the chapter name into the loader's
    // toString(). Read it once so each Stub gets a stable testid.
    const src = loader.toString();
    const match = src.match(/Chapter\d+\w+/);
    const name = match ? match[0] : "ChapterUnknown";
    return function ChapterStub() {
      return React.createElement(
        "section",
        { "data-testid": `stub-${name}` },
        name,
      );
    };
  },
}));

beforeEach(() => undefined);
afterEach(() => cleanup());

function wrap(node: React.ReactElement) {
  return render(
    <TranslationProvider>{node}</TranslationProvider>,
  );
}

describe("HomePage — composition", () => {
  it("mounts SiteHeader, ChapterRail, PageMeta, SiteFooter (CursorFlashlight is global, see layout.tsx)", async () => {
    const { default: HomePage } = await import("../HomePage");
    const { getByTestId } = wrap(<HomePage />);
    expect(getByTestId("stub-site-header")).toBeInTheDocument();
    expect(getByTestId("stub-chapter-rail")).toBeInTheDocument();
    expect(getByTestId("stub-page-meta")).toBeInTheDocument();
    expect(getByTestId("stub-site-footer")).toBeInTheDocument();
  });

  it("renders a <main> landmark for the chapter content", async () => {
    const { default: HomePage } = await import("../HomePage");
    const { container } = wrap(<HomePage />);
    expect(container.querySelector("main")).not.toBeNull();
  });

  it("mounts all 8 chapters via next/dynamic in correct order", async () => {
    const { default: HomePage } = await import("../HomePage");
    const { container } = wrap(<HomePage />);
    const main = container.querySelector("main");
    expect(main).not.toBeNull();
    const chapters = Array.from(
      main?.querySelectorAll("[data-testid^='stub-Chapter']") ?? [],
    ).map((el) => el.getAttribute("data-testid"));
    expect(chapters).toEqual([
      "stub-Chapter01TheWall",
      "stub-Chapter02TheNumbers",
      "stub-Chapter03MeetCarlos",
      "stub-Chapter04TheMap",
      "stub-Chapter05ThePlan",
      "stub-Chapter06LiveJobs",
      "stub-Chapter07TheCliff",
      "stub-Chapter08FindYourPath",
    ]);
  });
});
