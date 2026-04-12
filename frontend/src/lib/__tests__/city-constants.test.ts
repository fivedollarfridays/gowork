import { describe, it, expect } from "vitest";
import {
  isValidCityZip,
  isValidMontgomeryZip,
  getCareerCenter,
  getProgramLabels,
  getCityLabel,
  getCityAreaDescription,
  getZipPlaceholder,
  getZipErrorMessage,
  getJobBoardUrl,
  getLegalServicesUrl,
  getHousingUrl,
  getChildcareUrl,
  getBenefitsFallbackUrl,
  CAREER_CENTER_AL,
  CAREER_CENTER_TX,
} from "../constants";

describe("isValidCityZip", () => {
  it("validates Montgomery ZIPs for AL", () => {
    expect(isValidCityZip("36104", "AL")).toBe(true);
    expect(isValidCityZip("76102", "AL")).toBe(false);
  });

  it("validates Fort Worth ZIPs for TX", () => {
    expect(isValidCityZip("76102", "TX")).toBe(true);
    expect(isValidCityZip("36104", "TX")).toBe(false);
  });

  it("defaults to Montgomery when no state given", () => {
    expect(isValidCityZip("36104")).toBe(true);
    expect(isValidCityZip("76102")).toBe(false);
  });
});

describe("isValidMontgomeryZip (backward compat)", () => {
  it("still works for Montgomery ZIPs", () => {
    expect(isValidMontgomeryZip("36104")).toBe(true);
    expect(isValidMontgomeryZip("76102")).toBe(false);
  });
});

describe("getCareerCenter", () => {
  it("returns Montgomery career center for AL", () => {
    const cc = getCareerCenter("AL");
    expect(cc.name).toContain("Montgomery");
  });

  it("returns Fort Worth career center for TX", () => {
    const cc = getCareerCenter("TX");
    expect(cc.name).toContain("Workforce Solutions");
  });

  it("defaults to Montgomery", () => {
    const cc = getCareerCenter();
    expect(cc).toEqual(CAREER_CENTER_AL);
  });
});

describe("getProgramLabels", () => {
  it("returns AL labels by default", () => {
    const labels = getProgramLabels();
    expect(labels.ALL_Kids).toBe("ALL Kids");
    expect(labels.LIHEAP).toBe("LIHEAP");
  });

  it("returns TX labels for TX", () => {
    const labels = getProgramLabels("TX");
    expect(labels.CHIP).toBe("CHIP");
    expect(labels.CEAP).toBe("CEAP");
    expect(labels.ALL_Kids).toBeUndefined();
  });
});

describe("getCityLabel", () => {
  it("returns Montgomery, AL by default", () => {
    expect(getCityLabel()).toBe("Montgomery, AL");
  });

  it("returns Fort Worth, TX for TX", () => {
    expect(getCityLabel("TX")).toBe("Fort Worth, TX");
  });
});

describe("getCityAreaDescription", () => {
  it("returns Montgomery area description by default", () => {
    const desc = getCityAreaDescription();
    expect(desc).toContain("Montgomery");
  });

  it("returns Fort Worth area description for TX", () => {
    const desc = getCityAreaDescription("TX");
    expect(desc).toContain("Fort Worth");
  });
});

describe("getZipPlaceholder", () => {
  it("returns 36104 for AL", () => {
    expect(getZipPlaceholder()).toBe("36104");
  });

  it("returns 76102 for TX", () => {
    expect(getZipPlaceholder("TX")).toBe("76102");
  });
});

describe("getZipErrorMessage", () => {
  it("returns Montgomery error for AL", () => {
    const msg = getZipErrorMessage();
    expect(msg).toContain("Montgomery");
    expect(msg).toContain("361xx");
  });

  it("returns Fort Worth error for TX", () => {
    const msg = getZipErrorMessage("TX");
    expect(msg).toContain("Fort Worth");
    expect(msg).toContain("761xx");
  });
});

describe("city-aware URL functions", () => {
  it("getJobBoardUrl returns Alabama JobLink for AL", () => {
    expect(getJobBoardUrl()).toContain("joblink.alabama.gov");
  });

  it("getJobBoardUrl returns WorkInTexas for TX", () => {
    expect(getJobBoardUrl("TX")).toContain("workintexas.com");
  });

  it("getLegalServicesUrl returns AL legal services for AL", () => {
    expect(getLegalServicesUrl()).toContain("legalservicesalabama");
  });

  it("getLegalServicesUrl returns Legal Aid of NW Texas for TX", () => {
    expect(getLegalServicesUrl("TX")).toContain("lanwt.org");
  });

  it("getHousingUrl returns AL housing for AL", () => {
    expect(getHousingUrl()).toContain("hamd.org");
  });

  it("getHousingUrl returns Fort Worth housing for TX", () => {
    expect(getHousingUrl("TX")).toContain("fwhs.org");
  });

  it("getChildcareUrl returns AL childcare for AL", () => {
    expect(getChildcareUrl()).toContain("dhr.alabama.gov");
  });

  it("getChildcareUrl returns TX childcare for TX", () => {
    expect(getChildcareUrl("TX")).toContain("twc.texas.gov");
  });

  it("getBenefitsFallbackUrl returns AL for AL", () => {
    expect(getBenefitsFallbackUrl()).toContain("alabamabenefits");
  });

  it("getBenefitsFallbackUrl returns TX for TX", () => {
    expect(getBenefitsFallbackUrl("TX")).toContain("yourtexasbenefits");
  });
});
