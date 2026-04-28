"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { report } from "@/lib/error-reporter";

interface SectionErrorBoundaryProps {
  /** Section identifier reported to telemetry. */
  sectionName: string;
  children: ReactNode;
  /** Optional override of the default fallback UI. */
  fallback?: ReactNode;
}

interface SectionErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  resetKey: number;
}

/**
 * SectionErrorBoundary (T1.115).
 *
 * Class-based React error boundary scoped to a single section. When a
 * child throws during render, the boundary:
 *
 * 1. Renders the fallback (custom prop, or a minimal default labelled
 *    with the sectionName).
 * 2. Calls the error reporter (T1.117) with `{ section }` context.
 * 3. Exposes a "Try again" button that resets the boundary so the
 *    children get re-mounted (the retry path).
 *
 * NOTE: Driver C's `ErrorState` (T1.44) is the canonical pretty
 * fallback; consumers can pass it in via the `fallback` prop. Keeping
 * the default fallback dependency-free here so this component compiles
 * standalone in the W1 driver-B branch.
 */
export class SectionErrorBoundary extends Component<
  SectionErrorBoundaryProps,
  SectionErrorBoundaryState
> {
  state: SectionErrorBoundaryState = { hasError: false, error: null, resetKey: 0 };

  static getDerivedStateFromError(error: Error): Pick<SectionErrorBoundaryState, "hasError" | "error"> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    report(error, {
      section: this.props.sectionName,
      componentStack: info.componentStack ?? "",
    });
  }

  resetError = (): void => {
    this.setState((s) => ({ hasError: false, error: null, resetKey: s.resetKey + 1 }));
  };

  render(): ReactNode {
    if (!this.state.hasError) {
      return <div key={this.state.resetKey}>{this.props.children}</div>;
    }
    if (this.props.fallback) return this.props.fallback;
    return (
      <div
        data-testid="section-error-fallback"
        role="alert"
        style={{
          padding: "1.5rem",
          border: "1px solid var(--accent-cyan, #22D3EE)",
          borderRadius: "8px",
          color: "var(--fg-primary, #F5F3EE)",
          background: "var(--bg-surface, #0F1727)",
        }}
      >
        <p style={{ marginBottom: "0.75rem" }}>
          A problem rendered <strong>{this.props.sectionName}</strong>. The rest of the
          page is fine.
        </p>
        <button
          type="button"
          data-testid="section-error-retry"
          onClick={this.resetError}
          style={{
            padding: "0.4rem 0.8rem",
            background: "transparent",
            color: "var(--accent-cyan, #22D3EE)",
            border: "1px solid var(--accent-cyan, #22D3EE)",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          Try again
        </button>
      </div>
    );
  }
}
