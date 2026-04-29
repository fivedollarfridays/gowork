/**
 * polish-2 T55 — EyebrowActiveBridge tests.
 *
 * The bridge tracks the active chapter section via IntersectionObserver
 * and toggles `data-eyebrow-active="true"` on the section that occupies
 * ≥40% of the viewport. CSS rule (home-velocity.css) reads that attr
 * and lifts the eyebrow numeric to font-weight 700.
 */
import React from "react";
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, cleanup, act } from "@testing-library/react";

interface ObserverInstance {
  cb: IntersectionObserverCallback;
  options: IntersectionObserverInit | undefined;
  observed: Element[];
  disconnect: () => void;
  unobserve: (e: Element) => void;
}

const observers: ObserverInstance[] = [];

class MockIntersectionObserver {
  cb: IntersectionObserverCallback;
  options: IntersectionObserverInit | undefined;
  observed: Element[] = [];
  constructor(cb: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    this.cb = cb;
    this.options = options;
    observers.push(this as unknown as ObserverInstance);
  }
  observe(e: Element) {
    this.observed.push(e);
  }
  unobserve(e: Element) {
    this.observed = this.observed.filter((o) => o !== e);
  }
  disconnect() {
    this.observed = [];
  }
  takeRecords() {
    return [];
  }
  root = null;
  rootMargin = "";
  thresholds: number[] = [];
}

beforeEach(() => {
  observers.length = 0;
  Object.defineProperty(window, "IntersectionObserver", {
    value: MockIntersectionObserver,
    writable: true,
    configurable: true,
  });
});

afterEach(() => {
  cleanup();
  observers.length = 0;
});

import { EyebrowActiveBridge } from "../EyebrowActiveBridge";

function fireEntry(target: Element, intersectionRatio: number, isIntersecting: boolean) {
  const observer = observers[0];
  expect(observer).toBeDefined();
  act(() => {
    observer.cb(
      [
        {
          target,
          intersectionRatio,
          isIntersecting,
          boundingClientRect: target.getBoundingClientRect(),
          intersectionRect: target.getBoundingClientRect(),
          rootBounds: null,
          time: 0,
        } as IntersectionObserverEntry,
      ],
      observer as unknown as IntersectionObserver,
    );
  });
}

describe("EyebrowActiveBridge (polish-2 T55)", () => {
  it("creates an IntersectionObserver with a ≥0.4 threshold", () => {
    document.body.innerHTML =
      '<section class="chapter ch01" data-chapter-id="1"></section>';
    render(<EyebrowActiveBridge />);
    expect(observers).toHaveLength(1);
    const thresholds = observers[0].options?.threshold;
    const arr = Array.isArray(thresholds) ? thresholds : [thresholds];
    expect(arr.some((t) => typeof t === "number" && t >= 0.4)).toBe(true);
  });

  it("observes every section.chapter on the page", () => {
    document.body.innerHTML =
      '<section class="chapter ch01"></section><section class="chapter ch02"></section><section class="chapter ch03"></section>';
    render(<EyebrowActiveBridge />);
    expect(observers[0].observed.length).toBe(3);
  });

  it("sets data-eyebrow-active='true' on the section at ≥40% intersection", () => {
    document.body.innerHTML =
      '<section id="ch4" class="chapter ch04"></section>';
    render(<EyebrowActiveBridge />);
    const ch4 = document.getElementById("ch4")!;
    fireEntry(ch4, 0.6, true);
    expect(ch4.getAttribute("data-eyebrow-active")).toBe("true");
  });

  it("removes the attr when the section drops below 40%", () => {
    document.body.innerHTML =
      '<section id="chx" class="chapter ch04"></section>';
    render(<EyebrowActiveBridge />);
    const ch = document.getElementById("chx")!;
    fireEntry(ch, 0.6, true);
    expect(ch.getAttribute("data-eyebrow-active")).toBe("true");
    fireEntry(ch, 0.2, true);
    expect(ch.hasAttribute("data-eyebrow-active")).toBe(false);
  });

  it("only one section can be active at a time — switching deactivates the previous", () => {
    document.body.innerHTML =
      '<section id="ch4" class="chapter ch04"></section><section id="ch5" class="chapter ch05"></section>';
    render(<EyebrowActiveBridge />);
    const ch4 = document.getElementById("ch4")!;
    const ch5 = document.getElementById("ch5")!;
    fireEntry(ch4, 0.7, true);
    expect(ch4.getAttribute("data-eyebrow-active")).toBe("true");
    fireEntry(ch5, 0.7, true);
    expect(ch5.getAttribute("data-eyebrow-active")).toBe("true");
    expect(ch4.hasAttribute("data-eyebrow-active")).toBe(false);
  });
});
