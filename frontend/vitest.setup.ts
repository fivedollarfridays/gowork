import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// Global cleanup — runs after AND before every test in every file. Closes
// the parallel-test flake observed in PlanExport.test.tsx +
// CareerCenterExport.test.tsx where async chains (await fetch → flushSync
// → render print layout → await save) could leave React state mounted
// when the next test ran on Linux CI.
//
// Two-belt strategy:
//   1. afterEach drains microtasks then unmounts (covers tests that ended
//      before their async chain settled).
//   2. beforeEach nukes any residual document.body content as a backstop
//      (covers cases where afterEach unmount didn't catch a node attached
//      outside the RTL container — e.g., portals, CI timing edge cases).
afterEach(async () => {
  await new Promise((r) => setTimeout(r, 0));
  cleanup();
});

beforeEach(() => {
  // Belt-and-suspenders: ensure the DOM is genuinely empty at the top of
  // every test, not just after the previous test ran.
  if (typeof document !== "undefined") {
    document.body.innerHTML = "";
  }
});

// canvas-confetti uses requestAnimationFrame + canvas context which are unavailable
// in jsdom. Mock globally to prevent uncaught exceptions during parallel test runs.
vi.mock("canvas-confetti", () => ({ default: vi.fn() }));

// Radix UI components require ResizeObserver (not available in jsdom)
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Radix UI Select requires pointer capture methods (not available in jsdom)
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
  Element.prototype.setPointerCapture = () => {};
  Element.prototype.releasePointerCapture = () => {};
}

// Radix UI Select scrolls to focused item (not available in jsdom)
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

// framer-motion useInView requires IntersectionObserver (not available in jsdom)
if (!globalThis.IntersectionObserver) {
  globalThis.IntersectionObserver = class IntersectionObserver {
    constructor(_cb: IntersectionObserverCallback, _opts?: IntersectionObserverInit) {}
    observe() {}
    unobserve() {}
    disconnect() {}
    get root() { return null; }
    get rootMargin() { return ''; }
    get thresholds() { return []; }
    takeRecords() { return []; }
  } as unknown as typeof globalThis.IntersectionObserver;
}
