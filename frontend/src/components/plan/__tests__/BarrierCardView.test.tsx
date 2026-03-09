import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BarrierCardView } from "../BarrierCardView";
import { BarrierType } from "@/lib/types";
import type { BarrierCard, ExpungementResult } from "@/lib/types";

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
    expect(phoneLink).toHaveAttribute("href", "tel:3342861746");
  });

  it("renders address as a maps link", () => {
    render(<BarrierCardView barrier={barrier} />);

    const mapLink = screen.getByRole("link", { name: /1060 East South Boulevard/ });
    expect(mapLink.getAttribute("href")).toContain("google.com/maps/search");
    expect(mapLink.getAttribute("href")).toContain(
      encodeURIComponent("1060 East South Boulevard, Montgomery, AL 36116")
    );
  });
});

function makeRecordBarrier(expungement: ExpungementResult | null): BarrierCard {
  return {
    type: BarrierType.CRIMINAL_RECORD,
    severity: "medium",
    title: "Record & Legal Support",
    timeline_days: null,
    actions: ["Contact legal aid"],
    resources: [],
    transit_matches: [],
    expungement,
  };
}

describe("BarrierCardView expungement section", () => {
  it("shows eligible badge when eligible_now", () => {
    const card = makeRecordBarrier({
      eligibility: "eligible_now",
      years_remaining: 0,
      steps: ["Contact Legal Services Alabama"],
      filing_fee: "$300",
      notes: "You may be eligible to file now.",
    });
    render(<BarrierCardView barrier={card} />);
    expect(screen.getByText("May Be Eligible")).toBeInTheDocument();
    expect(screen.getByText("You may be eligible to file now.")).toBeInTheDocument();
  });

  it("shows future badge with years remaining", () => {
    const card = makeRecordBarrier({
      eligibility: "eligible_future",
      years_remaining: 3,
      steps: ["Wait 3 more years"],
      filing_fee: "$300",
      notes: "Eligible in approximately 3 years.",
    });
    render(<BarrierCardView barrier={card} />);
    expect(screen.getByText("3 years remaining")).toBeInTheDocument();
  });

  it("shows not eligible badge", () => {
    const card = makeRecordBarrier({
      eligibility: "not_eligible",
      years_remaining: null,
      steps: [],
      filing_fee: null,
      notes: "Not eligible under Alabama law.",
    });
    render(<BarrierCardView barrier={card} />);
    expect(screen.getByText("Not Eligible")).toBeInTheDocument();
  });

  it("hides expungement section when unknown", () => {
    const card = makeRecordBarrier({
      eligibility: "unknown",
      years_remaining: null,
      steps: [],
      filing_fee: null,
      notes: null,
    });
    render(<BarrierCardView barrier={card} />);
    expect(screen.queryByText("Expungement Eligibility")).not.toBeInTheDocument();
  });

  it("shows disclaimer", () => {
    const card = makeRecordBarrier({
      eligibility: "eligible_now",
      years_remaining: 0,
      steps: [],
      filing_fee: "$300",
      notes: null,
    });
    render(<BarrierCardView barrier={card} />);
    expect(screen.getByText(/not legal advice/)).toBeInTheDocument();
  });

  it("shows filing fee with waiver note", () => {
    const card = makeRecordBarrier({
      eligibility: "eligible_now",
      years_remaining: 0,
      steps: [],
      filing_fee: "$300",
      notes: null,
    });
    render(<BarrierCardView barrier={card} />);
    expect(screen.getByText(/\$300.*waivable/)).toBeInTheDocument();
  });

  it("hides expungement section when null", () => {
    const card = makeRecordBarrier(null);
    render(<BarrierCardView barrier={card} />);
    expect(screen.queryByText("Expungement Eligibility")).not.toBeInTheDocument();
  });
});
