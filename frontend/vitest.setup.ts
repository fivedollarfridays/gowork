import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// Global cleanup — runs after every test in every file, regardless of
// file-local afterEach hooks. Closes the parallel-test flake observed in
// PlanExport.test.tsx + CareerCenterExport.test.tsx (W1 souji notes) where
// async resolveSave() chains could leak React state into the next test.
// Two-phase cleanup: drain microtasks first (so any pending React state
// updates from `resolveSave()` commit), then unmount.
afterEach(async () => {
  await new Promise((r) => setTimeout(r, 0));
  cleanup();
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
