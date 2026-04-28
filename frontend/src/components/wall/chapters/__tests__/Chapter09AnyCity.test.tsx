/**
 * W3 Driver A — Chapter 09 Any City (T3.4, T3.5, T3.8).
 *
 * The continental finale of the FW chapter arc, before Ch10 (Driver C):
 *   - 2 lit cities: Fort Worth + Montgomery
 *   - 6 dotted future cities (Dallas, Houston, Atlanta, Memphis, Charlotte, Birmingham)
 *   - stat band: "5,189 tests · 13 sprints · 2 cities · MIT"
 *   - "Fly to Montgomery" + "Return to Fort Worth" buttons
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { setLocale } from "@/lib/i18n";
import { Chapter09AnyCity } from "../Chapter09AnyCity";

describe("Chapter09AnyCity — copy + structure", () => {
  beforeEach(() => setLocale("en"));

  it("renders the locked hero from i18n", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    expect(screen.getByTestId("ch9-hero").textContent).toMatch(
      /Fort Worth.*Montgomery/i,
    );
  });

  it("renders the stat band including MIT and city count", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    const stat = screen.getByTestId("ch9-stat-value").textContent ?? "";
    expect(stat).toMatch(/MIT/);
    expect(stat).toMatch(/cities/);
  });

  it("declares data-chapter='09' on its root", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    expect(
      screen.getByTestId("chapter09-any-city").getAttribute("data-chapter"),
    ).toBe("09");
  });

  it("renders Spanish hero when locale is es", () => {
    setLocale("es");
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    expect(screen.getByTestId("ch9-hero").textContent).toMatch(
      /Funciona en Fort Worth/i,
    );
    setLocale("en");
  });

  it("uses an h2 heading with id used by aria-labelledby", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    const root = screen.getByTestId("chapter09-any-city");
    const h2 = root.querySelector("h2");
    expect(h2).not.toBeNull();
    expect(root.getAttribute("aria-labelledby")).toBe(h2!.id);
  });
});

describe("Chapter09AnyCity — lit cities + future cities", () => {
  beforeEach(() => setLocale("en"));

  it("renders Fort Worth as a lit city", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    expect(screen.getByTestId("ch9-city-fw")).toBeInTheDocument();
    expect(screen.getByTestId("ch9-city-fw").getAttribute("data-lit")).toBe(
      "true",
    );
  });

  it("renders Montgomery as a lit city", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    expect(screen.getByTestId("ch9-city-montgomery")).toBeInTheDocument();
    expect(
      screen.getByTestId("ch9-city-montgomery").getAttribute("data-lit"),
    ).toBe("true");
  });

  it("renders 6 dotted future cities", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    const future = screen.getAllByTestId(/^ch9-city-future-/);
    expect(future.length).toBe(6);
    for (const c of future) {
      expect(c.getAttribute("data-lit")).toBe("false");
    }
  });
});

describe("Chapter09AnyCity — flyTo Montgomery + return buttons", () => {
  beforeEach(() => setLocale("en"));

  it("renders Fly-to-Montgomery as a button (not a div) for keyboard reach", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    const btn = screen.getByTestId("ch9-fly-to-montgomery");
    expect(btn.tagName).toBe("BUTTON");
  });

  it("renders Return-to-Fort-Worth as a button", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    const btn = screen.getByTestId("ch9-return-to-fw");
    expect(btn.tagName).toBe("BUTTON");
  });

  it("Fly button calls the optional onFlyToMontgomery callback when clicked", () => {
    const onFly = vi.fn();
    render(
      <Chapter09AnyCity
        progress={0.5}
        active={true}
        onFlyToMontgomery={onFly}
      />,
    );
    fireEvent.click(screen.getByTestId("ch9-fly-to-montgomery"));
    expect(onFly).toHaveBeenCalledTimes(1);
  });

  it("Return button calls the optional onReturnToFortWorth callback when clicked", () => {
    const onReturn = vi.fn();
    render(
      <Chapter09AnyCity
        progress={0.5}
        active={true}
        onReturnToFortWorth={onReturn}
      />,
    );
    fireEvent.click(screen.getByTestId("ch9-return-to-fw"));
    expect(onReturn).toHaveBeenCalledTimes(1);
  });

  it("buttons have accessible names from i18n", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} />);
    expect(
      screen.getByRole("button", { name: /Fly to Montgomery/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Return to Fort Worth/i }),
    ).toBeInTheDocument();
  });
});

describe("Chapter09AnyCity — a11y narration on activation", () => {
  beforeEach(() => setLocale("en"));

  it("emits aria-live narration when active", () => {
    const heard: string[] = [];
    function listener(e: Event) {
      heard.push((e as CustomEvent<string>).detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      render(<Chapter09AnyCity progress={0.05} active={true} />);
      expect(heard.some((m) => m.includes("Any City"))).toBe(true);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });

  it("does NOT emit narration when inactive", () => {
    const heard: string[] = [];
    function listener(e: Event) {
      heard.push((e as CustomEvent<string>).detail);
    }
    window.addEventListener("gowork:aria-announce", listener);
    try {
      render(<Chapter09AnyCity progress={0.05} active={false} />);
      expect(heard.length).toBe(0);
    } finally {
      window.removeEventListener("gowork:aria-announce", listener);
    }
  });
});

describe("Chapter09AnyCity — flyTo orchestrator integration (when map provided)", () => {
  let flyToSpy: ReturnType<typeof vi.fn>;
  let jumpToSpy: ReturnType<typeof vi.fn>;
  let fakeMap: import("../Chapter09AnyCity").Ch9FlyToMap;

  beforeEach(() => {
    setLocale("en");
    flyToSpy = vi.fn();
    jumpToSpy = vi.fn();
    fakeMap = {
      flyTo: flyToSpy as unknown as import("../Chapter09AnyCity").Ch9FlyToMap["flyTo"],
      jumpTo: jumpToSpy as unknown as import("../Chapter09AnyCity").Ch9FlyToMap["jumpTo"],
    };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("clicking Fly-to-Montgomery triggers map.flyTo with Montgomery coords", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} map={fakeMap} />);
    fireEvent.click(screen.getByTestId("ch9-fly-to-montgomery"));
    expect(flyToSpy).toHaveBeenCalledTimes(1);
    const arg = flyToSpy.mock.calls[0][0];
    expect(arg.center[0]).toBeCloseTo(-86.28, 2);
    expect(arg.center[1]).toBeCloseTo(32.36, 2);
  });

  it("clicking Return-to-Fort-Worth triggers map.flyTo with FW coords", () => {
    render(<Chapter09AnyCity progress={0.5} active={true} map={fakeMap} />);
    fireEvent.click(screen.getByTestId("ch9-return-to-fw"));
    expect(flyToSpy).toHaveBeenCalledTimes(1);
    const arg = flyToSpy.mock.calls[0][0];
    expect(arg.center[0]).toBeCloseTo(-97.3308, 3);
    expect(arg.center[1]).toBeCloseTo(32.7555, 3);
  });

  it("respects reducedMotion by routing through map.jumpTo", () => {
    render(
      <Chapter09AnyCity
        progress={0.5}
        active={true}
        map={fakeMap}
        reducedMotion={true}
      />,
    );
    fireEvent.click(screen.getByTestId("ch9-fly-to-montgomery"));
    expect(jumpToSpy).toHaveBeenCalledTimes(1);
    expect(flyToSpy).not.toHaveBeenCalled();
  });
});
