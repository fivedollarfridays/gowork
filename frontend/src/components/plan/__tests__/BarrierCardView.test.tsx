import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BarrierCardView } from "../BarrierCardView";
import { BarrierType } from "@/lib/types";
import type { BarrierCard } from "@/lib/types";

const barrier: BarrierCard = {
  type: BarrierType.TRANSPORTATION,
  severity: "high",
  title: "Transportation Access",
  timeline_days: null,
  actions: ["Review M-Transit routes"],
  resources: [
    {
      id: 1,
      name: "Montgomery Career Center",
      category: "career_center",
      subcategory: null,
      address: "1060 East South Boulevard, Montgomery, AL 36116",
      phone: "334-286-1746",
      url: null,
      eligibility: null,
      services: null,
      notes: null,
    },
  ],
  transit_matches: [],
};

describe("BarrierCardView clickable contacts", () => {
  it("renders phone number as a tel: link", () => {
    render(<BarrierCardView barrier={barrier} />);

    const phoneLink = screen.getByRole("link", { name: /334-286-1746/ });
    expect(phoneLink).toHaveAttribute("href", "tel:334-286-1746");
  });

  it("renders address as a maps link", () => {
    render(<BarrierCardView barrier={barrier} />);

    const mapLink = screen.getByRole("link", { name: /1060 East South Boulevard/ });
    expect(mapLink.getAttribute("href")).toContain("maps.google.com");
    expect(mapLink.getAttribute("href")).toContain(
      encodeURIComponent("1060 East South Boulevard, Montgomery, AL 36116")
    );
  });
});
