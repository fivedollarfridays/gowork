import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TransitInfoDisplay } from "../TransitInfoDisplay";
import type { TransitInfoDetail, RouteFeasibility } from "@/lib/types";

function makeRoute(overrides: Partial<RouteFeasibility> = {}): RouteFeasibility {
  return {
    route_number: 1,
    route_name: "Day Street",
    nearest_stop: "Rosa Parks Transfer Center",
    walk_miles: 0.2,
    first_bus: "05:00",
    last_bus: "21:00",
    has_sunday: false,
    feasible: true,
    ...overrides,
  };
}

function makeTransitInfo(overrides: Partial<TransitInfoDetail> = {}): TransitInfoDetail {
  return {
    serving_routes: [makeRoute()],
    transfer_count: 0,
    warnings: [],
    google_maps_url: null,
    ...overrides,
  };
}

describe("TransitInfoDisplay", () => {
  it("renders nothing when transit_info is null", () => {
    const { container } = render(<TransitInfoDisplay transitInfo={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when transit_info is undefined", () => {
    const { container } = render(<TransitInfoDisplay transitInfo={undefined} />);
    expect(container.firstChild).toBeNull();
  });

  it("shows route badges with number and name", () => {
    render(<TransitInfoDisplay transitInfo={makeTransitInfo()} />);
    expect(screen.getByText(/#1 Day Street/)).toBeInTheDocument();
  });

  it("shows multiple route badges", () => {
    const info = makeTransitInfo({
      serving_routes: [
        makeRoute({ route_number: 1, route_name: "Day Street" }),
        makeRoute({ route_number: 2, route_name: "Capitol Heights" }),
      ],
    });
    render(<TransitInfoDisplay transitInfo={info} />);
    expect(screen.getByText(/#1 Day Street/)).toBeInTheDocument();
    expect(screen.getByText(/#2 Capitol Heights/)).toBeInTheDocument();
  });

  it("shows walk distance", () => {
    render(<TransitInfoDisplay transitInfo={makeTransitInfo()} />);
    expect(screen.getByText(/0\.2 mi walk/)).toBeInTheDocument();
  });

  it("shows nearest stop name", () => {
    render(<TransitInfoDisplay transitInfo={makeTransitInfo()} />);
    expect(screen.getByText(/Rosa Parks/)).toBeInTheDocument();
  });

  it("shows Sunday gap warning", () => {
    const info = makeTransitInfo({ warnings: ["sunday_gap"] });
    render(<TransitInfoDisplay transitInfo={info} />);
    expect(screen.getByText(/no Sunday/i)).toBeInTheDocument();
  });

  it("shows night gap warning", () => {
    const info = makeTransitInfo({ warnings: ["night_gap"] });
    render(<TransitInfoDisplay transitInfo={info} />);
    expect(screen.getByText(/no night/i)).toBeInTheDocument();
  });

  it("shows long walk warning", () => {
    const info = makeTransitInfo({
      serving_routes: [makeRoute({ walk_miles: 0.8 })],
      warnings: ["long_walk"],
    });
    render(<TransitInfoDisplay transitInfo={info} />);
    expect(screen.getByText(/long walk/i)).toBeInTheDocument();
  });

  it("shows transfer info when transfers needed", () => {
    const info = makeTransitInfo({ transfer_count: 1 });
    render(<TransitInfoDisplay transitInfo={info} />);
    expect(screen.getByText(/1 transfer/i)).toBeInTheDocument();
  });

  it("shows Google Maps link when URL provided", () => {
    const info = makeTransitInfo({
      google_maps_url: "https://www.google.com/maps/dir/test?travelmode=transit",
    });
    render(<TransitInfoDisplay transitInfo={info} />);
    const link = screen.getByRole("link", { name: /plan your trip/i });
    expect(link).toHaveAttribute("href", info.google_maps_url);
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("hides Google Maps link when no URL", () => {
    render(<TransitInfoDisplay transitInfo={makeTransitInfo()} />);
    expect(screen.queryByRole("link", { name: /plan your trip/i })).not.toBeInTheDocument();
  });

  it("shows no routes message when serving_routes is empty", () => {
    const info = makeTransitInfo({ serving_routes: [] });
    render(<TransitInfoDisplay transitInfo={info} />);
    expect(screen.getByText(/no bus routes/i)).toBeInTheDocument();
  });

  it("shows infeasible route indicator", () => {
    const info = makeTransitInfo({
      serving_routes: [makeRoute({ feasible: false })],
    });
    render(<TransitInfoDisplay transitInfo={info} />);
    expect(screen.getByText(/schedule conflict/i)).toBeInTheDocument();
  });

  it("shows first and last bus schedule per route", () => {
    render(<TransitInfoDisplay transitInfo={makeTransitInfo()} />);
    expect(screen.getByText(/#1: 05:00–21:00/)).toBeInTheDocument();
  });

  it("shows schedule for multiple routes", () => {
    const info = makeTransitInfo({
      serving_routes: [
        makeRoute({ route_number: 1, first_bus: "05:00", last_bus: "21:00" }),
        makeRoute({ route_number: 2, first_bus: "06:00", last_bus: "20:30" }),
      ],
    });
    render(<TransitInfoDisplay transitInfo={info} />);
    expect(screen.getByText(/#1: 05:00–21:00/)).toBeInTheDocument();
    expect(screen.getByText(/#2: 06:00–20:30/)).toBeInTheDocument();
  });

  it("has aria-label on transit info container", () => {
    render(<TransitInfoDisplay transitInfo={makeTransitInfo()} />);
    expect(screen.getByLabelText("Transit information")).toBeInTheDocument();
  });

  it("has aria-label on route badges", () => {
    render(<TransitInfoDisplay transitInfo={makeTransitInfo()} />);
    expect(screen.getByLabelText("Route 1 Day Street")).toBeInTheDocument();
  });

  it("warnings section has status role", () => {
    const info = makeTransitInfo({ warnings: ["sunday_gap"] });
    render(<TransitInfoDisplay transitInfo={info} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
