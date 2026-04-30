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

/**
 * Reference deployment defaults flipped from Montgomery, AL → Fort Worth, TX
 * (see backend/app/core/config.py + lib/city-constants.ts). The Alabama
 * codepaths are still reachable when callers explicitly pass `"AL"`; the
 * "default" tests below now pin the Fort Worth side so subpages that don't
 * thread state stay on-brand for HackFW.
 */

describe("isValidCityZip", () => {
  it("validates Montgomery ZIPs for AL", () => {
    expect(isValidCityZip("36104", "AL")).toBe(true);
    expect(isValidCityZip("76102", "AL")).toBe(false);
  });

  it("validates Fort Worth ZIPs for TX", () => {
    expect(isValidCityZip("76102", "TX")).toBe(true);
    expect(isValidCityZip("36104", "TX")).toBe(false);
  });

  it("defaults to Fort Worth when no state given", () => {
    expect(isValidCityZip("76102")).toBe(true);
    expect(isValidCityZip("36104")).toBe(false);
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

  it("defaults to Fort Worth", () => {
    const cc = getCareerCenter();
    expect(cc).toEqual(CAREER_CENTER_TX);
  });
});

describe("getProgramLabels", () => {
  it("returns TX labels by default", () => {
    const labels = getProgramLabels();
    expect(labels.CHIP).toBe("CHIP");
    expect(labels.CEAP).toBe("CEAP");
  });

  it("returns AL labels for AL", () => {
    const labels = getProgramLabels("AL");
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
  it("returns Fort Worth, TX by default", () => {
    expect(getCityLabel()).toBe("Fort Worth, TX");
  });

  it("returns Montgomery, AL for AL", () => {
    expect(getCityLabel("AL")).toBe("Montgomery, AL");
  });

  it("returns Fort Worth, TX for TX", () => {
    expect(getCityLabel("TX")).toBe("Fort Worth, TX");
  });
});

describe("getCityAreaDescription", () => {
  it("returns Fort Worth area description by default", () => {
    const desc = getCityAreaDescription();
    expect(desc).toContain("Fort Worth");
  });

  it("returns Montgomery area description for AL", () => {
    const desc = getCityAreaDescription("AL");
    expect(desc).toContain("Montgomery");
  });

  it("returns Fort Worth area description for TX", () => {
    const desc = getCityAreaDescription("TX");
    expect(desc).toContain("Fort Worth");
  });
});

describe("getZipPlaceholder", () => {
  it("returns 76102 by default (Fort Worth)", () => {
    expect(getZipPlaceholder()).toBe("76102");
  });

  it("returns 36104 for AL", () => {
    expect(getZipPlaceholder("AL")).toBe("36104");
  });

  it("returns 76102 for TX", () => {
    expect(getZipPlaceholder("TX")).toBe("76102");
  });
});

describe("getZipErrorMessage", () => {
  it("returns Fort Worth error by default", () => {
    const msg = getZipErrorMessage();
    expect(msg).toContain("Fort Worth");
    expect(msg).toContain("761xx");
  });

  it("returns Montgomery error for AL", () => {
    const msg = getZipErrorMessage("AL");
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
  it("getJobBoardUrl defaults to WorkInTexas", () => {
    expect(getJobBoardUrl()).toContain("workintexas.com");
  });

  it("getJobBoardUrl returns Alabama JobLink for AL", () => {
    expect(getJobBoardUrl("AL")).toContain("joblink.alabama.gov");
  });

  it("getJobBoardUrl returns WorkInTexas for TX", () => {
    expect(getJobBoardUrl("TX")).toContain("workintexas.com");
  });

  it("getLegalServicesUrl defaults to Legal Aid of NW Texas", () => {
    expect(getLegalServicesUrl()).toContain("lanwt.org");
  });

  it("getLegalServicesUrl returns AL legal services for AL", () => {
    expect(getLegalServicesUrl("AL")).toContain("legalservicesalabama");
  });

  it("getLegalServicesUrl returns Legal Aid of NW Texas for TX", () => {
    expect(getLegalServicesUrl("TX")).toContain("lanwt.org");
  });

  it("getHousingUrl defaults to Fort Worth housing", () => {
    expect(getHousingUrl()).toContain("fwhs.org");
  });

  it("getHousingUrl returns AL housing for AL", () => {
    expect(getHousingUrl("AL")).toContain("hamd.org");
  });

  it("getHousingUrl returns Fort Worth housing for TX", () => {
    expect(getHousingUrl("TX")).toContain("fwhs.org");
  });

  it("getChildcareUrl defaults to TX childcare", () => {
    expect(getChildcareUrl()).toContain("twc.texas.gov");
  });

  it("getChildcareUrl returns AL childcare for AL", () => {
    expect(getChildcareUrl("AL")).toContain("dhr.alabama.gov");
  });

  it("getChildcareUrl returns TX childcare for TX", () => {
    expect(getChildcareUrl("TX")).toContain("twc.texas.gov");
  });

  it("getBenefitsFallbackUrl defaults to TX (yourtexasbenefits)", () => {
    expect(getBenefitsFallbackUrl()).toContain("yourtexasbenefits");
  });

  it("getBenefitsFallbackUrl returns AL for AL", () => {
    expect(getBenefitsFallbackUrl("AL")).toContain("alabamabenefits");
  });

  it("getBenefitsFallbackUrl returns TX for TX", () => {
    expect(getBenefitsFallbackUrl("TX")).toContain("yourtexasbenefits");
  });
});

// CAREER_CENTER_AL is still exported for AL-explicit callers.
describe("CAREER_CENTER_AL constant", () => {
  it("is the Montgomery career center", () => {
    expect(CAREER_CENTER_AL.name).toContain("Montgomery");
  });
});
