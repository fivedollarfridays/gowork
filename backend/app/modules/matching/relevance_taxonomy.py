"""Static taxonomies used by the resume<->job relevance scorer.

Splitting this out keeps relevance_scorer.py under the project's
400-line / 15-function ceiling without weakening the dictionaries.
"""

from __future__ import annotations

import re

# -- Certification taxonomy ------------------------------------------------
# Canonical name -> alternative spellings/regex patterns seen in resumes
CERTS: dict[str, list[str]] = {
    "RN": [r"\bRN\b", r"\bregistered\s+nurse\b", r"\bR\.?N\.?\b"],
    "BSN": [r"\bBSN\b"],
    "BLS": [r"\bBLS\b", r"basic life support"],
    "ACLS": [r"\bACLS\b", r"advanced cardiac life support"],
    "PALS": [r"\bPALS\b"],
    "CNA": [r"\bCNA\b", r"certified nursing assistant"],
    "LPN": [r"\bLPN\b", r"licensed practical nurse"],
    "LVN": [r"\bLVN\b"],
    "EMT": [r"\bEMT\b", r"emergency medical technician"],
    "MA": [r"\bmedical assistant\b"],
    "ServSafe": [r"\bservsafe\b", r"serv\s*safe"],
    "OSHA-10": [r"OSHA[\s-]?10"],
    "OSHA-30": [r"OSHA[\s-]?30"],
    "CDL": [r"\bCDL\b", r"\bCDL[\s-]?[ABC]\b"],
    "CDL-A": [r"\bCDL[\s-]?A\b", r"\bclass\s+a\s+CDL\b"],
    "GED": [r"\bGED\b"],
    "PMP": [r"\bPMP\b"],
    "AWS": [r"\bAWS\b"],
    "Forklift": [r"forklift\s+(?:cert|operator|certif)"],
    "GMP": [r"\bGMP\b", r"good manufacturing practice"],
    "AS9100": [r"\bAS9100\b"],
    "ISO_9001": [r"\bISO\s*9001\b"],
}

# -- Title taxonomy --------------------------------------------------------
# Title keyword -> job_family slug.  Keep keys lowercased so callers can
# do straight substring lookups against lower(text).
TITLE_FAMILY: dict[str, str] = {
    "registered nurse": "nursing",
    "rn ": "nursing",
    "nurse": "nursing",
    "lpn": "nursing",
    "lvn": "nursing",
    "cna": "nursing_aide",
    "patient care": "nursing_aide",
    "certified nursing assistant": "nursing_aide",
    "medical assistant": "medical_office",
    "phlebotomy": "medical_office",
    "phlebotomist": "medical_office",
    "pharmacy tech": "pharmacy",
    "med tech": "medical_office",
    "forklift": "warehouse",
    "warehouse": "warehouse",
    "picker": "warehouse",
    "packer": "warehouse",
    "loader": "warehouse",
    "stocker": "warehouse",
    "yard": "warehouse",
    "driver": "driving",
    "trucker": "driving",
    "cdl": "driving",
    "delivery": "driving",
    "courier": "driving",
    "welder": "welding",
    "welding": "welding",
    "electrician": "electrical",
    "plumber": "plumbing",
    "carpenter": "carpentry",
    "construction": "general_construction",
    "laborer": "general_construction",
    "concrete": "general_construction",
    "roofer": "general_construction",
    "hvac": "hvac",
    "machinist": "manufacturing",
    "machine operator": "manufacturing",
    "production": "manufacturing",
    "assembly": "manufacturing",
    "fabricator": "manufacturing",
    "quality control": "manufacturing",
    "cook": "kitchen",
    "chef": "kitchen",
    "kitchen": "kitchen",
    "dishwasher": "kitchen",
    "server": "front_of_house",
    "barista": "front_of_house",
    "cashier": "front_of_house",
    "customer service": "customer_service",
    "csr": "customer_service",
    "call center": "customer_service",
    "ramp agent": "airline_ground",
    "gate agent": "airline_ground",
    "baggage": "airline_ground",
    "custodian": "custodial",
    "janitor": "custodial",
    "housekeeper": "custodial",
    "security": "security",
    "guard": "security",
    "office assistant": "office_admin",
    "administrative assistant": "office_admin",
    "clerk": "office_admin",
    "receptionist": "office_admin",
    "data entry": "office_admin",
    "teacher": "education",
    "teaching assistant": "education",
    "paraprofessional": "education",
}

# -- Family -> industry mapping -------------------------------------------
FAMILY_INDUSTRY: dict[str, str] = {
    "nursing": "healthcare",
    "nursing_aide": "healthcare",
    "medical_office": "healthcare",
    "pharmacy": "healthcare",
    "warehouse": "manufacturing",
    "driving": "transportation",
    "welding": "construction",
    "electrical": "construction",
    "plumbing": "construction",
    "carpentry": "construction",
    "general_construction": "construction",
    "hvac": "construction",
    "manufacturing": "manufacturing",
    "kitchen": "food_service",
    "front_of_house": "food_service",
    "customer_service": "retail",
    "airline_ground": "transportation",
    "custodial": "manufacturing",
    "security": "government",
    "office_admin": "government",
    "education": "government",
}

# -- Years experience extraction patterns ---------------------------------
YEARS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(\d{1,2})\s*\+?\s*years?", re.IGNORECASE),
    re.compile(r"(\d{1,2})\s*yrs?", re.IGNORECASE),
]

# -- Education level ranking ---------------------------------------------
EDU_LEVELS: dict[str, int] = {
    "high_school": 1, "ged": 1,
    "associate": 2, "associates": 2,
    "bachelor": 3, "bachelors": 3, "bs": 3, "ba": 3, "bsn": 3,
    "master": 4, "masters": 4, "ms": 4, "ma_degree": 4, "mba": 4,
    "doctorate": 5, "phd": 5, "md": 5,
}
