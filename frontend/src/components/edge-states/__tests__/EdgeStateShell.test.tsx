/**
 * polish-2 Driver D — EdgeStateShell tests.
 *
 * Locks the contract for the shared shell consumed by 404 / 500 / loading:
 *   - Tags itself with `[data-edge-state="<kind>"]`
 *   - Mounts the Ch1 background (`.ch01-bg`) so edge states feel like the
 *     same site, not a separate failure surface.
 *   - Eyebrow + headline + body + CTA all render in the expected slots.
 *   - The shell renders a `<main id="main">` landmark so SkipToContent
 *     still has a target on edge routes.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EdgeStateShell } from "../EdgeStateShell";

describe("EdgeStateShell — contract", () => {
  it("tags the section with data-edge-state for the requested kind (404)", () => {
    const { container } = render(
      <EdgeStateShell kind="404" eyebrow="404" headline="Lost" />,
    );
    expect(container.querySelector('[data-edge-state="404"]')).not.toBeNull();
  });

  it("mounts the Ch1 background (`.ch01-bg`) inside the shell", () => {
    const { container } = render(
      <EdgeStateShell kind="404" eyebrow="404" headline="Lost" />,
    );
    expect(container.querySelector(".ch01-bg")).not.toBeNull();
  });

  it("renders eyebrow, headline, body, and CTA", () => {
    render(
      <EdgeStateShell
        kind="500"
        eyebrow="500"
        headline="The wall stayed up"
        body="We are rebuilding."
        cta={<button type="button">retry</button>}
      />,
    );
    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText("The wall stayed up")).toBeInTheDocument();
    expect(screen.getByText("We are rebuilding.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("renders a main#main landmark for SkipToContent target", () => {
    const { container } = render(
      <EdgeStateShell kind="404" eyebrow="404" headline="Lost" />,
    );
    expect(container.querySelector("main#main")).not.toBeNull();
  });

  it("supports the loading kind tag", () => {
    const { container } = render(
      <EdgeStateShell kind="loading" eyebrow="…" headline="Calibrating" />,
    );
    expect(container.querySelector('[data-edge-state="loading"]')).not.toBeNull();
  });
});
