import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResourceMap, type MapResource } from "../ResourceMap";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

const SAMPLE_RESOURCES: MapResource[] = [
  {
    id: 1,
    name: "Workforce Solutions for Tarrant County",
    category: "career_center",
    address: "1200 Circle Dr, Fort Worth, TX 76119",
    phone: "817-413-4400",
    url: "https://workforcesolutions.net",
  },
  {
    id: 2,
    name: "Catholic Charities Fort Worth",
    category: "housing",
    address: "249 W Thornhill Dr, Fort Worth, TX 76115",
    phone: "817-289-0011",
    url: null,
  },
  {
    id: 3,
    name: "Tarrant County Food Bank",
    category: "food",
    address: "2600 Cullen St, Fort Worth, TX 76107",
    phone: "817-332-9177",
    url: "https://tafb.org",
  },
];

function renderMap(resources = SAMPLE_RESOURCES) {
  return render(
    <TranslationProvider>
      <ResourceMap resources={resources} />
    </TranslationProvider>,
  );
}

describe("ResourceMap", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders heading", () => {
    renderMap();
    expect(screen.getByText(/community resources/i)).toBeInTheDocument();
  });

  it("renders all resource names", () => {
    renderMap();
    expect(screen.getByText("Workforce Solutions for Tarrant County")).toBeInTheDocument();
    expect(screen.getByText("Catholic Charities Fort Worth")).toBeInTheDocument();
    expect(screen.getByText("Tarrant County Food Bank")).toBeInTheDocument();
  });

  it("renders resource addresses", () => {
    renderMap();
    expect(screen.getByText(/1200 Circle Dr/)).toBeInTheDocument();
  });

  it("renders phone numbers as links", () => {
    renderMap();
    const phoneLinks = screen.getAllByRole("link", { name: /817-/ });
    expect(phoneLinks.length).toBeGreaterThanOrEqual(1);
  });

  it("renders directions links", () => {
    renderMap();
    const directionLinks = screen.getAllByText(/get directions/i);
    expect(directionLinks.length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty state when no resources", () => {
    renderMap([]);
    expect(screen.getByText(/no resources found/i)).toBeInTheDocument();
  });

  it("groups resources by category", () => {
    renderMap();
    // Category headers should appear (exact text from humanizeCategory)
    expect(screen.getByText("Career Center")).toBeInTheDocument();
    expect(screen.getByText("Housing")).toBeInTheDocument();
    expect(screen.getByText("Food")).toBeInTheDocument();
  });

  it("renders in Spanish when locale is ES", () => {
    setLocale("es");
    renderMap();
    expect(screen.getByText(/recursos comunitarios/i)).toBeInTheDocument();
  });

  it("renders website links when available", () => {
    renderMap();
    const websiteLinks = screen.getAllByText(/website/i);
    // 2 resources have URLs
    expect(websiteLinks.length).toBe(2);
  });
});
