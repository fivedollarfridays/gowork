/**
 * Tests for AppointmentsCounter — Driver D Spotlight invention #5.
 *
 * After GoWork sequences the path, Carlos has FEWER appointments — the
 * Spotlight invention shows that count visually. It's the W3-prep
 * complement to FormsCounter (47 → ?). Decoupled from W3 so we can
 * demonstrate the contract today.
 */
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { AppointmentsCounter } from "../AppointmentsCounter";

describe("AppointmentsCounter — counts down with progress", () => {
  it("renders the maxAppointments at progress 0", () => {
    const { getByTestId } = render(
      <AppointmentsCounter
        progress={0}
        maxAppointments={47}
        minAppointments={5}
      />,
    );
    expect(getByTestId("appointments-counter-value").textContent).toBe("47");
  });

  it("renders the minAppointments at progress 1", () => {
    const { getByTestId } = render(
      <AppointmentsCounter
        progress={1}
        maxAppointments={47}
        minAppointments={5}
      />,
    );
    expect(getByTestId("appointments-counter-value").textContent).toBe("5");
  });

  it("interpolates linearly between max and min across progress", () => {
    const { getByTestId } = render(
      <AppointmentsCounter
        progress={0.5}
        maxAppointments={47}
        minAppointments={5}
      />,
    );
    const value = parseInt(
      getByTestId("appointments-counter-value").textContent ?? "0",
      10,
    );
    expect(value).toBeGreaterThan(20);
    expect(value).toBeLessThan(35);
  });

  it("clamps progress below 0 to 0 and above 1 to 1", () => {
    const { getByTestId, rerender } = render(
      <AppointmentsCounter
        progress={-5}
        maxAppointments={47}
        minAppointments={5}
      />,
    );
    expect(getByTestId("appointments-counter-value").textContent).toBe("47");
    rerender(
      <AppointmentsCounter
        progress={5}
        maxAppointments={47}
        minAppointments={5}
      />,
    );
    expect(getByTestId("appointments-counter-value").textContent).toBe("5");
  });

  it("emits an aria-label that announces the current count", () => {
    const { getByTestId } = render(
      <AppointmentsCounter
        progress={0}
        maxAppointments={47}
        minAppointments={5}
      />,
    );
    const wrapper = getByTestId("appointments-counter");
    expect(wrapper.getAttribute("aria-label")).toMatch(/47/);
  });

  it("announces a status role for screen-reader pickup", () => {
    const { getByTestId } = render(
      <AppointmentsCounter
        progress={0.5}
        maxAppointments={47}
        minAppointments={5}
      />,
    );
    expect(getByTestId("appointments-counter").getAttribute("role")).toBe(
      "status",
    );
  });

  it("snaps to min when reducedMotion=true (no transition class)", () => {
    const { getByTestId } = render(
      <AppointmentsCounter
        progress={0.5}
        maxAppointments={47}
        minAppointments={5}
        reducedMotion
      />,
    );
    const wrapper = getByTestId("appointments-counter");
    expect(wrapper.getAttribute("data-reduced-motion")).toBe("true");
  });
});
