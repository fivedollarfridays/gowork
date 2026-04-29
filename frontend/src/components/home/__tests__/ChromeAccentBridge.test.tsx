/**
 * ChromeAccentBridge — polish-2 T4.
 *
 * As each chapter enters the viewport ≥50%, the bridge sets `--chrome-accent`
 * on `:root` to that chapter's signature accent. Header CTA bg + brand-mark
 * glow + header bottom border read `var(--chrome-accent)`.
 *
 * Mapping (signature accents):
 *   Ch1=cyan, Ch2=amber, Ch3=amber, Ch4=cyan, Ch5=amber,
 *   Ch6=status-positive, Ch7=rose, Ch8=cyan.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, act } from "@testing-library/react";
import { ChromeAccentBridge } from "../ChromeAccentBridge";

type IOInstance = {
  observe: ReturnType<typeof vi.fn>;
  unobserve: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
  callback: IntersectionObserverCallback;
  options: IntersectionObserverInit | undefined;
  trigger: (entries: Partial<IntersectionObserverEntry>[]) => void;
};

let lastIO: IOInstance | null = null;

function installIO(): void {
  globalThis.IntersectionObserver = class {
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
    constructor(
      private cb: IntersectionObserverCallback,
      private opts?: IntersectionObserverInit,
    ) {
      lastIO = {
        observe: this.observe,
        unobserve: this.unobserve,
        disconnect: this.disconnect,
        callback: cb,
        options: opts,
        trigger: (entries) => {
          this.cb(entries as IntersectionObserverEntry[], this as unknown as IntersectionObserver);
        },
      };
    }
    get root() {
      return null;
    }
    get rootMargin() {
      return "";
    }
    get thresholds() {
      return [];
    }
    takeRecords() {
      return [] as IntersectionObserverEntry[];
    }
  } as unknown as typeof globalThis.IntersectionObserver;
}

function makeChapterSection(idx: number): HTMLElement {
  const s = document.createElement("section");
  s.id = `chapter-${idx.toString().padStart(2, "0")}`;
  document.body.appendChild(s);
  return s;
}

describe("ChromeAccentBridge — chapter accent leak", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    document.documentElement.style.removeProperty("--chrome-accent");
    lastIO = null;
    installIO();
  });

  afterEach(() => {
    document.body.innerHTML = "";
    document.documentElement.style.removeProperty("--chrome-accent");
  });

  it("renders nothing visible (effect-only component)", () => {
    const { container } = render(<ChromeAccentBridge />);
    expect(container.firstChild).toBeNull();
  });

  it("observes all 8 chapter sections after mount", () => {
    for (let i = 1; i <= 8; i++) makeChapterSection(i);
    render(<ChromeAccentBridge />);
    expect(lastIO).not.toBeNull();
    expect(lastIO!.observe).toHaveBeenCalledTimes(8);
  });

  it("sets --chrome-accent to rose when Ch7 becomes ≥50% visible", () => {
    for (let i = 1; i <= 8; i++) makeChapterSection(i);
    render(<ChromeAccentBridge />);
    const section7 = document.getElementById("chapter-07")!;
    act(() => {
      lastIO!.trigger([
        { target: section7, isIntersecting: true, intersectionRatio: 0.6 },
      ]);
    });
    const accent = document.documentElement.style.getPropertyValue("--chrome-accent").trim();
    // Should resolve to the rose accent token.
    expect(accent).toBe("var(--accent-rose)");
  });

  it("sets --chrome-accent to amber when Ch2 becomes ≥50% visible", () => {
    for (let i = 1; i <= 8; i++) makeChapterSection(i);
    render(<ChromeAccentBridge />);
    const section2 = document.getElementById("chapter-02")!;
    act(() => {
      lastIO!.trigger([
        { target: section2, isIntersecting: true, intersectionRatio: 0.55 },
      ]);
    });
    const accent = document.documentElement.style.getPropertyValue("--chrome-accent").trim();
    expect(accent).toBe("var(--accent-amber)");
  });

  it("sets --chrome-accent to status-positive when Ch6 enters", () => {
    for (let i = 1; i <= 8; i++) makeChapterSection(i);
    render(<ChromeAccentBridge />);
    const section6 = document.getElementById("chapter-06")!;
    act(() => {
      lastIO!.trigger([
        { target: section6, isIntersecting: true, intersectionRatio: 0.7 },
      ]);
    });
    const accent = document.documentElement.style.getPropertyValue("--chrome-accent").trim();
    expect(accent).toBe("var(--status-positive)");
  });

  it("disconnects the IntersectionObserver on unmount", () => {
    for (let i = 1; i <= 8; i++) makeChapterSection(i);
    const { unmount } = render(<ChromeAccentBridge />);
    unmount();
    expect(lastIO!.disconnect).toHaveBeenCalled();
  });
});
