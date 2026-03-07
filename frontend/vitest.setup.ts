import "@testing-library/jest-dom/vitest";

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
