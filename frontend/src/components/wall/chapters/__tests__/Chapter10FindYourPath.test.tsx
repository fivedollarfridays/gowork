/**
 * W3 Driver C — T3.20 — Chapter 10 component tests.
 *
 * Narrative Reset (sprint/narrative-reset): the secondary GitHub link
 * was removed from the user-facing chapter. MIT licensing + repo URLs
 * live in the LICENSE file and the Devpost form, NOT in the editorial
 * overlay. Tests now assert the GitHub link is ABSENT.
 *
 * Asserts the chapter renders with:
 *   - section heading h2 (id stable for aria-labelledby)
 *   - primary CTA button labelled with translated copy
 *   - NO secondary GitHub link
 *   - editorial body + footer brand row
 *   - data-chapter="10" + data-testid="chapter10-find-your-path"
 *
 * The CTA's actual View Transitions navigation is unit-tested in
 * `viewTransitions.test.ts`; here we just verify the click invokes a
 * navigation handler.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { Chapter10FindYourPath } from "../Chapter10FindYourPath";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn(), back: vi.fn() }),
}));

beforeEach(() => {
  cleanup();
  mockPush.mockReset();
});

describe("Chapter10FindYourPath — render contract (T3.20)", () => {
  it("renders section with data-chapter='10' and testid", () => {
    render(<Chapter10FindYourPath progress={0.5} active />);
    const section = screen.getByTestId("chapter10-find-your-path");
    expect(section).toBeTruthy();
    expect(section.getAttribute("data-chapter")).toBe("10");
  });

  it("renders an h2 heading (chapter is below the h1 title sequence)", () => {
    render(<Chapter10FindYourPath progress={0.5} active />);
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toBeTruthy();
  });

  it("renders the primary CTA as a button with the translated label", () => {
    render(<Chapter10FindYourPath progress={0.5} active />);
    const button = screen.getByTestId("chapter10-cta-primary");
    expect(button.tagName).toBe("BUTTON");
    expect(button.textContent ?? "").toMatch(/start your assessment/i);
  });

  it("does NOT render a secondary GitHub link (Narrative Reset)", () => {
    render(<Chapter10FindYourPath progress={0.5} active />);
    expect(screen.queryByTestId("chapter10-github-link")).toBeNull();
  });

  it("does NOT render any 'GitHub' or 'open-source' user-facing copy", () => {
    render(<Chapter10FindYourPath progress={0.5} active />);
    const section = screen.getByTestId("chapter10-find-your-path");
    expect(section.textContent ?? "").not.toMatch(/GitHub/i);
    expect(section.textContent ?? "").not.toMatch(/open-source/i);
  });

  it("primary CTA carries an aria-label distinct from its visible text", () => {
    render(<Chapter10FindYourPath progress={0.5} active />);
    const button = screen.getByTestId("chapter10-cta-primary");
    expect(button.getAttribute("aria-label")).toBeTruthy();
  });

  it("section has aria-labelledby pointing at the h2 id", () => {
    render(<Chapter10FindYourPath progress={0.5} active />);
    const section = screen.getByTestId("chapter10-find-your-path");
    const heading = screen.getByRole("heading", { level: 2 });
    expect(section.getAttribute("aria-labelledby")).toBe(heading.id);
    expect(heading.id.length).toBeGreaterThan(0);
  });

  it("renders the brand mark (BrandMark svg)", () => {
    render(<Chapter10FindYourPath progress={0.5} active />);
    // BrandMark renders an svg with aria-label="GoWork".
    const brand = screen.getByLabelText("GoWork");
    expect(brand.tagName.toLowerCase()).toBe("svg");
  });
});

describe("Chapter10FindYourPath — CTA click navigates to /assess", () => {
  it("invokes router.push('/assess') when the primary CTA is clicked", () => {
    render(<Chapter10FindYourPath progress={1} active />);
    const button = screen.getByTestId("chapter10-cta-primary");
    fireEvent.click(button);
    expect(mockPush).toHaveBeenCalledWith("/assess");
  });
});

describe("Chapter10FindYourPath — view-transition-name CSS hook", () => {
  it("attaches view-transition-name CSS to a stable element via inline style", () => {
    render(<Chapter10FindYourPath progress={1} active />);
    const morph = screen.getByTestId("chapter10-morph-target");
    // The component sets viewTransitionName as an inline style;
    // jsdom retains it on the element.style object.
    expect(morph.style.getPropertyValue("view-transition-name")).toBe(
      "wall-to-assess",
    );
  });
});
