import { describe, it, expect, vi, afterEach } from "vitest";
import { render, fireEvent } from "@testing-library/react";

vi.mock("../../../lib/error-reporter", () => ({
  report: vi.fn(),
}));

import { report } from "../../../lib/error-reporter";
import { SectionErrorBoundary } from "../SectionErrorBoundary";

function Boom({ explode }: { explode: boolean }): JSX.Element {
  if (explode) throw new Error("kaboom");
  return <span>safe</span>;
}

afterEach(() => {
  vi.mocked(report).mockClear();
});

describe("SectionErrorBoundary (T1.115)", () => {
  it("renders children when no error", () => {
    const { getByText } = render(
      <SectionErrorBoundary sectionName="chapter-1">
        <Boom explode={false} />
      </SectionErrorBoundary>,
    );
    expect(getByText("safe")).toBeTruthy();
  });

  it("renders default fallback with sectionName when child throws", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { getByTestId } = render(
      <SectionErrorBoundary sectionName="chapter-1">
        <Boom explode={true} />
      </SectionErrorBoundary>,
    );
    const fb = getByTestId("section-error-fallback");
    expect(fb.textContent).toContain("chapter-1");
    errorSpy.mockRestore();
  });

  it("calls error reporter once with sectionName context", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <SectionErrorBoundary sectionName="chapter-1">
        <Boom explode={true} />
      </SectionErrorBoundary>,
    );
    expect(report).toHaveBeenCalledTimes(1);
    const ctx = vi.mocked(report).mock.calls[0][1];
    expect(ctx?.section).toBe("chapter-1");
    errorSpy.mockRestore();
  });

  it("retry button resets the boundary so children re-mount", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    let shouldExplode = true;
    function Toggleable(): JSX.Element {
      // Reads the closure each render; once we click retry and switch
      // the closure to false, the next render is safe.
      return <Boom explode={shouldExplode} />;
    }
    const { getByTestId, queryByTestId } = render(
      <SectionErrorBoundary sectionName="chapter-1">
        <Toggleable />
      </SectionErrorBoundary>,
    );
    expect(getByTestId("section-error-fallback")).toBeTruthy();
    shouldExplode = false;
    fireEvent.click(getByTestId("section-error-retry"));
    expect(queryByTestId("section-error-fallback")).toBeNull();
    errorSpy.mockRestore();
  });

  it("uses a custom fallback render prop when provided", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { getByText } = render(
      <SectionErrorBoundary
        sectionName="chapter-1"
        fallback={<div>Custom Fallback Here</div>}
      >
        <Boom explode={true} />
      </SectionErrorBoundary>,
    );
    expect(getByText("Custom Fallback Here")).toBeTruthy();
    errorSpy.mockRestore();
  });
});
