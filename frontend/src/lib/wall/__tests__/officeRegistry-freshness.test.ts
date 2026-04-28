/**
 * Spotlight invention — Real-data verification freshness gate.
 *
 * Asserts that every office's `sourceDate` is within 180 days of the
 * test-runtime clock. A failure means a verification has gone stale and
 * a reviewer should re-cross-check the listing before submission.
 *
 * 180 days is an explicit honest-uncertainty acknowledgement: government
 * office hours change rarely; addresses change less. A tighter window
 * (e.g., 30 days) would force needless reviewer cycles. A looser window
 * (e.g., 365 days) would let pre-submission staleness slip through.
 *
 * # Lens: Honesty (forensic truth)
 *
 * The brief said "verify primary sources" once. This gate makes the
 * verification testable, not just promised. If T2.68/T2.69/T2.70/T2.71/
 * T2.72 are not refreshed before submission, this test fails — visible
 * to the reviewer agent.
 */

import { describe, it, expect } from "vitest";
import { TARRANT_OFFICES } from "../officeRegistry";

const MAX_AGE_DAYS = 180;

describe("officeRegistry freshness gate", () => {
  it("every office's sourceDate is within 180 days of test runtime", () => {
    const now = Date.now();
    for (const office of TARRANT_OFFICES) {
      const date = Date.parse(office.sourceDate);
      expect(Number.isFinite(date)).toBe(true);
      const ageDays = (now - date) / (1000 * 60 * 60 * 24);
      // Allow future-dated entries (the dispatch is dated 2026-04-27;
      // this test must be portable across CI clocks).
      const ageBounded = Math.max(0, ageDays);
      expect(ageBounded).toBeLessThanOrEqual(MAX_AGE_DAYS);
    }
  });

  it("every office's sourceUrl uses HTTPS (transport-level provenance)", () => {
    for (const office of TARRANT_OFFICES) {
      expect(office.sourceUrl.startsWith("https://")).toBe(true);
    }
  });
});
