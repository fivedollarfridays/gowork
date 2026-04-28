/**
 * W1 Driver C — T1.41 branded 500 error page.
 *
 * Asserts :
 *   - Title from i18n (edge.500.title) renders.
 *   - Body copy mentions "calibrating" — the locked motif from the dispatch.
 *   - The CTA invokes the `reset` callback when clicked.
 *   - The route renders a `main#main` landmark.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { setLocale } from "@/lib/i18n";
import ErrorPage from "../error";

describe("/error — T1.41 branded 500", () => {
  const fakeError = new Error("boom") as Error & { digest?: string };
  fakeError.digest = "abc123";

  beforeEach(() => {
    setLocale("en");
  });

  it("renders the branded title", () => {
    render(<ErrorPage error={fakeError} reset={() => {}} />);
    expect(
      screen.getByRole("heading", { name: /something stalled/i }),
    ).toBeInTheDocument();
  });

  it("body copy keeps the calibrating motif", () => {
    render(<ErrorPage error={fakeError} reset={() => {}} />);
    expect(screen.getByText(/calibrat/i)).toBeInTheDocument();
  });

  it("CTA invokes the reset callback when clicked", () => {
    const reset = vi.fn();
    render(<ErrorPage error={fakeError} reset={reset} />);
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(reset).toHaveBeenCalledTimes(1);
  });

  it("renders a main landmark with id=main for skip-to-content compatibility", () => {
    const { container } = render(
      <ErrorPage error={fakeError} reset={() => {}} />,
    );
    expect(container.querySelector("main#main")).toBeInTheDocument();
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    render(<ErrorPage error={fakeError} reset={() => {}} />);
    expect(
      screen.getByRole("heading", { name: /algo se detuvo/i }),
    ).toBeInTheDocument();
  });

  it("does NOT leak error.message into the rendered UI", () => {
    render(<ErrorPage error={fakeError} reset={() => {}} />);
    expect(screen.queryByText(/boom/i)).not.toBeInTheDocument();
  });
});
