/**
 * Matches resume text to recommended industries and certifications
 * using keyword-based scoring. No LLM needed — deterministic and instant.
 */

const INDUSTRY_KEYWORDS: Record<string, string[]> = {
  healthcare: [
    "nurse", "nursing", "cna", "lpn", "rn", "medical", "hospital", "clinic",
    "patient", "healthcare", "health care", "pharmacy", "physician", "doctor",
    "therapist", "dental", "emt", "paramedic", "caregiver", "home health",
  ],
  manufacturing: [
    "manufacturing", "factory", "assembly", "machine", "operator", "production",
    "quality control", "warehouse", "forklift", "industrial", "welding", "welder",
  ],
  food_service: [
    "food", "restaurant", "server", "cook", "kitchen", "chef", "catering",
    "fast food", "barista", "waitress", "waiter", "dishwasher", "food service",
    "mcdonald", "burger", "pizza", "subway", "diner", "cafeteria",
  ],
  government: [
    "government", "federal", "state", "county", "municipal", "city",
    "public service", "civil service", "administration", "clerk", "postal",
  ],
  retail: [
    "retail", "cashier", "sales associate", "customer service", "store",
    "walmart", "target", "dollar", "merchandise", "stock", "inventory",
    "sales floor", "register",
  ],
  construction: [
    "construction", "carpenter", "electrician", "plumber", "hvac", "roofing",
    "concrete", "framing", "building", "contractor", "laborer", "mason",
  ],
  transportation: [
    "driver", "driving", "cdl", "truck", "delivery", "logistics", "shipping",
    "freight", "dispatch", "uber", "lyft", "bus", "transit", "courier",
  ],
};

const CERTIFICATION_KEYWORDS: Record<string, string[]> = {
  CNA: ["cna", "certified nursing assistant", "nursing assistant", "patient care"],
  CDL: ["cdl", "commercial driver", "truck driver", "class a", "class b"],
  LPN: ["lpn", "licensed practical nurse", "practical nurse", "nursing license"],
};

function scoreMatch(text: string, keywords: string[]): number {
  let score = 0;
  for (const kw of keywords) {
    if (text.includes(kw)) score++;
  }
  return score;
}

export interface ResumeRecommendations {
  industries: string[];
  certifications: string[];
}

export function getResumeRecommendations(resumeText: string): ResumeRecommendations {
  if (!resumeText || resumeText.trim().length === 0) {
    return { industries: [], certifications: [] };
  }

  const lower = resumeText.toLowerCase();

  const industries: string[] = [];
  for (const [industry, keywords] of Object.entries(INDUSTRY_KEYWORDS)) {
    if (scoreMatch(lower, keywords) >= 2) {
      industries.push(industry);
    }
  }

  const certifications: string[] = [];
  for (const [cert, keywords] of Object.entries(CERTIFICATION_KEYWORDS)) {
    if (scoreMatch(lower, keywords) >= 1) {
      certifications.push(cert);
    }
  }

  return { industries, certifications };
}
