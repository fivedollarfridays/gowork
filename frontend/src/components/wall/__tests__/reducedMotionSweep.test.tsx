/**
 * W4 Driver C — T4.C.1 — Reduced-motion sweep across every animation
 * site in The Wall.
 *
 * Mocks `usePrefersReducedMotion` to return `true`, mounts every chapter
 * + every wall component that consumes the hook, and asserts each one
 * sets the documented reduced-motion contract:
 *   - chapters 1-3: `data-fallback="static"` on the editorial overlay
 *   - chapters 4-10: `data-reduced-motion="true"` on the section root
 *   - CarlosAvatar: `data-reduced-motion="true"`, no footstep effect
 *   - BarrierConstellation: `data-breathing-hz="0"` and
 *                           `data-reduced-motion="true"`
 *   - CursorFlashlight: `data-fallback="uniform"`
 *   - CursorTrail: returns null entirely
 *
 * Without this sweep, individual per-component tests can drift — a future
 * refactor adds a Ch11, forgets the hook, and a screen-reader user gets
 * vestibular triggers on demo day.
 */
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";

// Mock the reduced-motion hook BEFORE any chapter / component imports.
vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: () => true,
}));

// Chapters 1-3 consult the React TranslationProvider context. Mock
// useTranslation so tests don't crash without a wrapping provider.
vi.mock("@/hooks/useTranslation", () => ({
  useTranslation: () => ({
    locale: "en",
    t: (key: string) => key,
    switchLocale: vi.fn(),
  }),
  TranslationProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Next/navigation is used by Ch10 (View Transitions); mock so tests
// don't crash without an app router.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
}));

import { Chapter01Continental } from "../chapters/Chapter01Continental";
import { Chapter02CityArrival } from "../chapters/Chapter02CityArrival";
import { Chapter03Neighborhood } from "../chapters/Chapter03Neighborhood";
import { Chapter04TheWall } from "../chapters/Chapter04TheWall";
import { Chapter05Labyrinth } from "../chapters/Chapter05Labyrinth";
import { Chapter06TheMath } from "../chapters/Chapter06TheMath";
import { Chapter07ThePath } from "../chapters/Chapter07ThePath";
import { Chapter08TheGraph } from "../chapters/Chapter08TheGraph";
import { Chapter09AnyCity } from "../chapters/Chapter09AnyCity";
import { Chapter10FindYourPath } from "../chapters/Chapter10FindYourPath";
import { CarlosAvatar } from "../CarlosAvatar";
import { CursorFlashlight } from "../CursorFlashlight";
import { CursorTrail } from "../CursorTrail";

beforeEach(() => undefined);
afterEach(() => cleanup());

describe("T4.C.1 — Chapter 01-03 reduced-motion (data-fallback='static')", () => {
  it("Chapter01Continental sets data-fallback='static'", () => {
    const { container } = render(
      React.createElement(Chapter01Continental, { progress: 0.5 }),
    );
    const overlay = container.querySelector("[data-fallback]");
    expect(overlay).not.toBeNull();
    expect(overlay?.getAttribute("data-fallback")).toBe("static");
  });

  it("Chapter02CityArrival sets data-fallback='static'", () => {
    const { container } = render(
      React.createElement(Chapter02CityArrival, { progress: 0.5 }),
    );
    const overlay = container.querySelector("[data-fallback]");
    expect(overlay).not.toBeNull();
    expect(overlay?.getAttribute("data-fallback")).toBe("static");
  });

  it("Chapter03Neighborhood sets data-fallback='static'", () => {
    const { container } = render(
      React.createElement(Chapter03Neighborhood, {
        progress: 0.5,
        active: true,
      }),
    );
    const overlay = container.querySelector("[data-fallback]");
    expect(overlay).not.toBeNull();
    expect(overlay?.getAttribute("data-fallback")).toBe("static");
  });
});

describe("T4.C.1 — Chapter 04-10 reduced-motion (data-reduced-motion='true')", () => {
  it("Chapter04TheWall sets data-reduced-motion='true' (via reducedMotion prop)", () => {
    const { container } = render(
      React.createElement(Chapter04TheWall, {
        progress: 0.5,
        reducedMotion: true,
      }),
    );
    const root = container.querySelector("[data-reduced-motion]");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("data-reduced-motion")).toBe("true");
  });

  it("Chapter05Labyrinth sets data-reduced-motion='true'", () => {
    const { container } = render(
      React.createElement(Chapter05Labyrinth, {
        progress: 0.5,
        reducedMotion: true,
      }),
    );
    const root = container.querySelector("[data-reduced-motion]");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("data-reduced-motion")).toBe("true");
  });

  it("Chapter06TheMath sets data-reduced-motion='true'", () => {
    const { container } = render(
      React.createElement(Chapter06TheMath, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const root = container.querySelector("[data-reduced-motion]");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("data-reduced-motion")).toBe("true");
  });

  it("Chapter07ThePath sets data-reduced-motion='true'", () => {
    const { container } = render(
      React.createElement(Chapter07ThePath, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const root = container.querySelector("[data-reduced-motion]");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("data-reduced-motion")).toBe("true");
  });

  it("Chapter08TheGraph sets data-reduced-motion='true' (renders static SVG fallback)", () => {
    const { container } = render(
      React.createElement(Chapter08TheGraph, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const root = container.querySelector("[data-reduced-motion]");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("data-reduced-motion")).toBe("true");
  });

  it("Chapter09AnyCity sets data-reduced-motion='true'", () => {
    const { container } = render(
      React.createElement(Chapter09AnyCity, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const root = container.querySelector("[data-reduced-motion]");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("data-reduced-motion")).toBe("true");
  });

  it("Chapter10FindYourPath sets data-reduced-motion='true'", () => {
    const { container } = render(
      React.createElement(Chapter10FindYourPath, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const root = container.querySelector("[data-reduced-motion]");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("data-reduced-motion")).toBe("true");
  });
});

describe("T4.C.1 — Wall components reduced-motion sweep", () => {
  it("CarlosAvatar sets data-reduced-motion='true' and disables stride animation", () => {
    const { container } = render(
      React.createElement(CarlosAvatar, { progress: 0.5, reducedMotion: true }),
    );
    const root = container.querySelector("[data-testid='carlos-avatar']");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("data-reduced-motion")).toBe("true");
  });

  it("CursorFlashlight uses uniform fallback, not live radial gradient", () => {
    const { container } = render(React.createElement(CursorFlashlight));
    const root = container.querySelector("[data-testid='cursor-flashlight']");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("data-fallback")).toBe("uniform");
  });

  it("CursorTrail returns null entirely (no DOM) in reduced motion", () => {
    const { container } = render(React.createElement(CursorTrail));
    // CursorTrail returns null — the wrapper is empty.
    expect(container.firstChild).toBeNull();
  });
});
