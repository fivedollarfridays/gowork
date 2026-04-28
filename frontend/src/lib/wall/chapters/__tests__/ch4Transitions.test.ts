/**
 * W2 Driver C — Ch4 sub-chapter transition orchestrator (T2.36).
 *
 * The transition module is map-instance-agnostic — it accepts an opaque
 * MapHandle (Driver A wires the real Mapbox map at integration time) and
 * a `prefersReducedMotion` flag. It returns a list of layer paint changes
 * (opacity targets) that the consumer applies. We test the shape of the
 * plan, not the Mapbox calls — that's Driver A's contract surface.
 */
import { describe, it, expect } from "vitest";
import {
  planCh4Transition,
  CH4_TRANSITION_DURATION_MS,
  CH4_TRANSITION_DURATION_REDUCED_MS,
} from "../ch4Transitions";

describe("planCh4Transition", () => {
  it("returns an empty plan when the sub-chapter is unchanged", () => {
    const plan = planCh4Transition("4a", "4a", false);
    expect(plan.changes).toHaveLength(0);
  });

  it("dims the previous office and lights the next one (Wave 5: ids aligned)", () => {
    const plan = planCh4Transition("4a", "4b", false);
    const dim = plan.changes.find((c) => c.officeId === "tarrant-district-clerk");
    const light = plan.changes.find(
      (c) => c.officeId === "tx-dps-mega-center-fort-worth",
    );
    expect(dim?.targetOpacity).toBe(0.4);
    expect(light?.targetOpacity).toBe(1.0);
  });

  it("uses the spring-soft duration when motion is allowed", () => {
    const plan = planCh4Transition("4a", "4b", false);
    expect(plan.durationMs).toBe(CH4_TRANSITION_DURATION_MS);
  });

  it("collapses to instant duration when reduced motion is on", () => {
    const plan = planCh4Transition("4a", "4b", true);
    expect(plan.durationMs).toBe(CH4_TRANSITION_DURATION_REDUCED_MS);
  });

  it("handles the 4d transition (no highlight office) without crashing (Wave 5: ids aligned)", () => {
    // 4c → 4d — 4d has no highlightOfficeId; only the prev dims.
    const plan = planCh4Transition("4c", "4d", false);
    expect(
      plan.changes.find(
        (c) => c.officeId === "hhsc-fort-worth-east-lancaster",
      )?.targetOpacity,
    ).toBe(0.4);
    // No light-up entry (4d highlights jobs, not an office).
    expect(plan.changes.length).toBe(1);
  });

  it("declares the 4d job-paint mutation flag for credit-check job markers", () => {
    const plan = planCh4Transition("4c", "4d", false);
    expect(plan.creditCheckJobsDimmed).toBe(true);
  });

  it("clears the 4d job-paint flag when leaving 4d", () => {
    const plan = planCh4Transition("4d", "4c", false);
    expect(plan.creditCheckJobsDimmed).toBe(false);
  });
});
