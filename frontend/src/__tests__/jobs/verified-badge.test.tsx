/**
 * T24.10 — VerifiedBadge component tests.
 *
 * The badge is purely display: it never affects matching, ranking, or
 * filtering (Sprint 24 charter integrity invariant; pinned independently
 * by T24.11). These tests exercise only the visual contract.
 */

import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { VerifiedBadge } from "@/components/jobs/VerifiedBadge";

describe("VerifiedBadge", () => {
  describe("null / missing tier", () => {
    it("renders nothing when tier is null (no hidden div)", () => {
      const { container } = render(
        <VerifiedBadge tier={null} intakeComplete={false} />,
      );
      // Whole render output should be empty — no wrapper, no a11y-hidden.
      expect(container.firstChild).toBeNull();
    });

    it("renders nothing when tier is null even if intakeComplete is true", () => {
      // intake_complete without a tier is a malformed backend payload.
      // We protect the UI by simply rendering nothing rather than
      // surfacing a half-state.
      const { container } = render(
        <VerifiedBadge tier={null} intakeComplete={true} />,
      );
      expect(container.firstChild).toBeNull();
    });
  });

  describe("source_trust tier", () => {
    it('renders "Source Verified" label', () => {
      render(<VerifiedBadge tier="source_trust" intakeComplete={false} />);
      expect(screen.getByText("Source Verified")).toBeInTheDocument();
    });

    it("uses paler cyan styling (bg-primary/40, distinct from claim_verified)", () => {
      render(<VerifiedBadge tier="source_trust" intakeComplete={false} />);
      const badge = screen.getByTestId("verified-badge-source_trust");
      // Paler variant must include the /40 opacity modifier on bg-primary.
      expect(badge.className).toContain("bg-primary/40");
    });

    it("exposes tooltip text via title attribute about source-feed origin", () => {
      render(<VerifiedBadge tier="source_trust" intakeComplete={false} />);
      const badge = screen.getByTestId("verified-badge-source_trust");
      const title = badge.getAttribute("title") ?? "";
      expect(title.toLowerCase()).toMatch(/source/);
    });
  });

  describe("claim_verified tier", () => {
    it('renders "Verified Employer" label', () => {
      render(<VerifiedBadge tier="claim_verified" intakeComplete={false} />);
      expect(screen.getByText("Verified Employer")).toBeInTheDocument();
    });

    it("uses full cyan styling (bg-primary, no /40 opacity)", () => {
      render(<VerifiedBadge tier="claim_verified" intakeComplete={false} />);
      const badge = screen.getByTestId("verified-badge-claim_verified");
      expect(badge.className).toContain("bg-primary");
      expect(badge.className).not.toContain("bg-primary/40");
    });

    it("exposes tooltip text mentioning employer claim", () => {
      render(<VerifiedBadge tier="claim_verified" intakeComplete={false} />);
      const badge = screen.getByTestId("verified-badge-claim_verified");
      const title = badge.getAttribute("title") ?? "";
      expect(title.toLowerCase()).toMatch(/employer/);
    });
  });

  describe("admin_reviewed tier", () => {
    it('renders "Verified Employer" label (same visual as claim_verified)', () => {
      render(<VerifiedBadge tier="admin_reviewed" intakeComplete={false} />);
      expect(screen.getByText("Verified Employer")).toBeInTheDocument();
    });

    it("uses full cyan styling — same as claim_verified", () => {
      render(<VerifiedBadge tier="admin_reviewed" intakeComplete={false} />);
      const badge = screen.getByTestId("verified-badge-admin_reviewed");
      expect(badge.className).toContain("bg-primary");
      expect(badge.className).not.toContain("bg-primary/40");
    });

    it("exposes tooltip text mentioning admin or staff review", () => {
      render(<VerifiedBadge tier="admin_reviewed" intakeComplete={false} />);
      const badge = screen.getByTestId("verified-badge-admin_reviewed");
      const title = badge.getAttribute("title") ?? "";
      // Admin-reviewed is a backstop tier when claim heuristic mismatches —
      // tooltip should signal the human-review provenance.
      expect(title.toLowerCase()).toMatch(/admin|review|staff/);
    });
  });

  describe("intake_complete sub-badge", () => {
    it('shows "+ Intake Complete" amber sub-badge when intakeComplete=true', () => {
      render(<VerifiedBadge tier="claim_verified" intakeComplete={true} />);
      const sub = screen.getByTestId("verified-badge-intake-complete");
      expect(sub).toBeInTheDocument();
      expect(sub.textContent).toMatch(/Intake Complete/);
      expect(sub.className).toContain("bg-warning");
    });

    it("does NOT render the sub-badge when intakeComplete=false", () => {
      render(<VerifiedBadge tier="claim_verified" intakeComplete={false} />);
      expect(
        screen.queryByTestId("verified-badge-intake-complete"),
      ).not.toBeInTheDocument();
    });

    it("renders sub-badge alongside source_trust tier too", () => {
      // Intake completeness is independent of tier — a source-trust
      // listing whose employer additionally completed intake should
      // surface both badges.
      render(<VerifiedBadge tier="source_trust" intakeComplete={true} />);
      expect(
        screen.getByTestId("verified-badge-source_trust"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("verified-badge-intake-complete"),
      ).toBeInTheDocument();
    });
  });
});
