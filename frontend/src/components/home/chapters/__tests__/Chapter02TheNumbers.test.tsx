/**
 * Chapter02TheNumbers — pinned, oversized counters (Driver B).
 *
 * Locks:
 *   - Section is data-bg=dark with aria-labelledby pointing at the heading.
 *   - Eyebrow "02 / The numbers".
 *   - 2x2 stat grid: 600,000+, 87 min, 7, $22.50/hr.
 *   - Each stat carries `data-target` for the count-up driver.
 *   - Pull quote at the bottom: "These aren't talking points. They're Tuesday."
 *   - Spanish toggle swaps headline + caption copy.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

import { Chapter02TheNumbers } from "../Chapter02TheNumbers";

beforeEach(() => setLocale("en"));
afterEach(() => {
  cleanup();
  setLocale("en");
});

function renderEn() {
  setLocale("en");
  return render(
    <TranslationProvider>
      <Chapter02TheNumbers />
    </TranslationProvider>,
  );
}

function renderEs() {
  setLocale("es");
  return render(
    <TranslationProvider>
      <Chapter02TheNumbers />
    </TranslationProvider>,
  );
}

describe("Chapter02TheNumbers — pinned counters", () => {
  it("renders a section with data-bg=dark", () => {
    const { container } = renderEn();
    expect(container.querySelector("section[data-bg='dark']")).not.toBeNull();
  });

  it("section has aria-labelledby pointing at an h2", () => {
    const { container } = renderEn();
    const section = container.querySelector("section[data-bg='dark']");
    const id = section?.getAttribute("aria-labelledby");
    expect(id).toBeTruthy();
    const heading = container.querySelector(`#${id}`);
    expect(heading?.tagName.toLowerCase()).toBe("h2");
  });

  it("renders four stats with the expected targets", () => {
    const { container } = renderEn();
    const stats = container.querySelectorAll("[data-stat]");
    expect(stats.length).toBe(4);
    const targets = Array.from(stats).map((s) =>
      s.getAttribute("data-target"),
    );
    expect(targets).toEqual(["600000", "87", "7", "22.50"]);
  });

  it("stat numbers display the human-formatted values in EN", () => {
    renderEn();
    expect(screen.getByText(/600,000\+/)).toBeInTheDocument();
    expect(screen.getByText(/87 min/)).toBeInTheDocument();
    expect(screen.getByText(/\$22\.50\/hr/)).toBeInTheDocument();
  });

  it("pull quote names Tuesday in English", () => {
    renderEn();
    expect(
      screen.getByText(/These aren't talking points/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Tuesday/i)).toBeInTheDocument();
  });

  it("Spanish toggle swaps caption copy", () => {
    renderEs();
    expect(screen.getByText(/Los números/i)).toBeInTheDocument();
    expect(screen.getByText(/No son frases/i)).toBeInTheDocument();
  });
});

describe("Chapter02TheNumbers — T14 locale-aware stat formatter", () => {
  it("renders 600.000+ with European thousands separators in ES", () => {
    renderEs();
    // ES grouping: dot-separated thousands. The "600,000+" English string
    // must NOT appear when locale=es.
    expect(screen.queryByText(/600,000\+/)).toBeNull();
    expect(screen.getByText(/600\.000\+/)).toBeInTheDocument();
  });

  it("renders 600,000+ with comma thousands separators in EN", () => {
    renderEn();
    expect(screen.getByText(/600,000\+/)).toBeInTheDocument();
  });
});

describe("Chapter02TheNumbers — T15 pull quote drop cap", () => {
  it("pull quote carries the ch02-pull class so the ::first-letter rule applies", () => {
    const { container } = renderEn();
    const pull = container.querySelector(".ch02-pull");
    expect(pull).not.toBeNull();
  });

  it("pull quote carries data-dropcap='on' so the drop-cap CSS rule triggers", () => {
    const { container } = renderEn();
    const pull = container.querySelector(".ch02-pull");
    expect(pull?.getAttribute("data-dropcap")).toBe("on");
  });
});
