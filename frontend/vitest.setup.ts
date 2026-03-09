import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

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
