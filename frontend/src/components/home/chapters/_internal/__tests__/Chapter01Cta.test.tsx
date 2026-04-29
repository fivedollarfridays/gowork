/**
 * Driver C — polish-2 T37 — minimal contract test for the Ch01 CTA.
 *
 * Chapter01Cta is owned primarily by Driver B; the only Driver-C touch is
 * mounting `useMagneticHover` + `useIdleState` and reflecting idle status
 * via `data-idle-orbit`. This test pins that integration without changing
 * the parent's behavior.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";
import { Chapter01Cta } from "../Chapter01Cta";

const idleMock = vi.fn();
vi.mock("@/hooks/useIdleState", () => ({
  useIdleState: (...args: unknown[]) => idleMock(...args),
}));

beforeEach(() => {
  idleMock.mockReset();
});
afterEach(() => {
  cleanup();
});

describe("Chapter01Cta — T37 idle-orbit", () => {
  it("renders the primary CTA with data-idle-orbit='true' when useIdleState returns true", () => {
    idleMock.mockReturnValue(true);
    const { container } = render(
      <Chapter01Cta primaryLabel="Get your plan" ghostLabel="See how it works" />,
    );
    const primary = container.querySelector(".cta-primary");
    expect(primary).not.toBeNull();
    expect(primary?.getAttribute("data-idle-orbit")).toBe("true");
  });

  it("renders data-idle-orbit='false' when not idle", () => {
    idleMock.mockReturnValue(false);
    const { container } = render(
      <Chapter01Cta primaryLabel="Get your plan" ghostLabel="See how it works" />,
    );
    const primary = container.querySelector(".cta-primary");
    expect(primary?.getAttribute("data-idle-orbit")).toBe("false");
  });

  it("primary CTA still points at /assess (Driver B's contract preserved)", () => {
    idleMock.mockReturnValue(false);
    const { container } = render(
      <Chapter01Cta primaryLabel="Get your plan" ghostLabel="See how it works" />,
    );
    const primary = container.querySelector(".cta-primary") as HTMLAnchorElement;
    expect(primary.getAttribute("href")).toBe("/assess");
  });
});
