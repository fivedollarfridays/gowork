/**
 * useMagneticHover — polish-2 T1.
 *
 * Pulls a target element toward the cursor when the cursor enters a
 * configurable proximity radius. Used on Ch1 hero primary CTA (T1) +
 * other CTAs by sibling drivers.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useMagneticHover } from "../useMagneticHover";

function setMatchMedia(matches: (q: string) => boolean): void {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: (query: string) => ({
      matches: matches(query),
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

function attachToDom(el: HTMLElement, rect: Partial<DOMRect>): void {
  document.body.appendChild(el);
  el.getBoundingClientRect = () =>
    ({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      width: 0,
      height: 0,
      toJSON: () => ({}),
      ...rect,
    }) as DOMRect;
}

describe("useMagneticHover — proximity pull", () => {
  let rafCb: FrameRequestCallback | null = null;

  beforeEach(() => {
    setMatchMedia(() => false);
    rafCb = null;
    vi.stubGlobal(
      "requestAnimationFrame",
      ((cb: FrameRequestCallback) => {
        rafCb = cb;
        return 1 as unknown as number;
      }) as typeof requestAnimationFrame,
    );
    vi.stubGlobal("cancelAnimationFrame", (() => {}) as typeof cancelAnimationFrame);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    document.body.innerHTML = "";
  });

  it("translates the element toward the cursor when within proximity", () => {
    const { result } = renderHook(() => useMagneticHover<HTMLAnchorElement>());
    const anchor = document.createElement("a");
    attachToDom(anchor, { left: 100, top: 100, right: 200, bottom: 140, width: 100, height: 40 });
    act(() => {
      (result.current as { current: HTMLAnchorElement | null }).current = anchor;
    });

    // Move cursor near the button: center is (150, 120). Place at (110, 80) so dx=-40, dy=-40.
    act(() => {
      window.dispatchEvent(
        new MouseEvent("mousemove", { clientX: 110, clientY: 80 }),
      );
    });
    // Drain a few rAF ticks to let lerp settle.
    for (let i = 0; i < 60; i++) {
      act(() => {
        if (rafCb) {
          const cb = rafCb;
          rafCb = null;
          cb(performance.now());
        }
      });
    }

    const transform = anchor.style.transform;
    expect(transform).toMatch(/translate3d\(-?\d+(\.\d+)?px, -?\d+(\.\d+)?px, 0\)/);
    // Cursor was up and to the left of the center; the element should pull
    // up-and-left, i.e. negative x AND negative y.
    const match = /translate3d\((-?\d+(?:\.\d+)?)px, (-?\d+(?:\.\d+)?)px/.exec(transform);
    expect(match).not.toBeNull();
    const x = parseFloat(match![1]);
    const y = parseFloat(match![2]);
    expect(x).toBeLessThan(0);
    expect(y).toBeLessThan(0);
    // And the magnitude should be capped at --magnetic-pull-max (default 10px).
    expect(Math.abs(x)).toBeLessThanOrEqual(10);
    expect(Math.abs(y)).toBeLessThanOrEqual(10);
  });

  it("returns to origin on pointerleave / mouseleave", () => {
    const { result } = renderHook(() => useMagneticHover<HTMLButtonElement>());
    const btn = document.createElement("button");
    attachToDom(btn, { left: 100, top: 100, right: 200, bottom: 140, width: 100, height: 40 });
    act(() => {
      (result.current as { current: HTMLButtonElement | null }).current = btn;
    });

    act(() => {
      window.dispatchEvent(new MouseEvent("mousemove", { clientX: 110, clientY: 80 }));
    });
    for (let i = 0; i < 80; i++) {
      act(() => {
        if (rafCb) {
          const cb = rafCb;
          rafCb = null;
          cb(performance.now());
        }
      });
    }
    expect(btn.style.transform).not.toBe("translate3d(0px, 0px, 0)");

    // Move cursor far away — outside proximity.
    act(() => {
      window.dispatchEvent(new MouseEvent("mousemove", { clientX: 2000, clientY: 2000 }));
    });
    for (let i = 0; i < 80; i++) {
      act(() => {
        if (rafCb) {
          const cb = rafCb;
          rafCb = null;
          cb(performance.now());
        }
      });
    }
    // After far-cursor + lerp settle, transform should be ≈ origin.
    const match = /translate3d\((-?\d+(?:\.\d+)?)px, (-?\d+(?:\.\d+)?)px/.exec(btn.style.transform);
    expect(match).not.toBeNull();
    expect(Math.abs(parseFloat(match![1]))).toBeLessThan(0.5);
    expect(Math.abs(parseFloat(match![2]))).toBeLessThan(0.5);
  });

  it("renders zero translation on coarse pointer (touch devices)", () => {
    setMatchMedia((q) => q.includes("coarse"));
    const { result } = renderHook(() => useMagneticHover<HTMLButtonElement>());
    const btn = document.createElement("button");
    attachToDom(btn, { left: 100, top: 100, right: 200, bottom: 140, width: 100, height: 40 });
    act(() => {
      (result.current as { current: HTMLButtonElement | null }).current = btn;
    });

    act(() => {
      window.dispatchEvent(new MouseEvent("mousemove", { clientX: 110, clientY: 80 }));
    });
    for (let i = 0; i < 30; i++) {
      act(() => {
        if (rafCb) {
          const cb = rafCb;
          rafCb = null;
          cb(performance.now());
        }
      });
    }
    expect(btn.style.transform).toBe("");
  });

  it("renders zero translation when prefers-reduced-motion is on", () => {
    setMatchMedia((q) => q.includes("reduced-motion"));
    const { result } = renderHook(() => useMagneticHover<HTMLButtonElement>());
    const btn = document.createElement("button");
    attachToDom(btn, { left: 100, top: 100, right: 200, bottom: 140, width: 100, height: 40 });
    act(() => {
      (result.current as { current: HTMLButtonElement | null }).current = btn;
    });

    act(() => {
      window.dispatchEvent(new MouseEvent("mousemove", { clientX: 110, clientY: 80 }));
    });
    for (let i = 0; i < 30; i++) {
      act(() => {
        if (rafCb) {
          const cb = rafCb;
          rafCb = null;
          cb(performance.now());
        }
      });
    }
    expect(btn.style.transform).toBe("");
  });

  it("respects the disabled option", () => {
    const { result } = renderHook(() => useMagneticHover<HTMLButtonElement>({ disabled: true }));
    const btn = document.createElement("button");
    attachToDom(btn, { left: 100, top: 100, right: 200, bottom: 140, width: 100, height: 40 });
    act(() => {
      (result.current as { current: HTMLButtonElement | null }).current = btn;
    });

    act(() => {
      window.dispatchEvent(new MouseEvent("mousemove", { clientX: 110, clientY: 80 }));
    });
    for (let i = 0; i < 30; i++) {
      act(() => {
        if (rafCb) {
          const cb = rafCb;
          rafCb = null;
          cb(performance.now());
        }
      });
    }
    expect(btn.style.transform).toBe("");
  });
});
