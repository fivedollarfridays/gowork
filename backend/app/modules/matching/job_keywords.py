"""Keyword maps for job matching: industry, schedule conflict, and skills extraction."""

INDUSTRY_KEYWORDS: dict[str, set[str]] = {
    "healthcare": {
        "nurse", "nursing", "cna", "medical", "hospital", "clinic",
        "patient", "health", "aide", "phlebotomy", "pharmacy", "dietary",
        "home health", "caregiver", "therapist",
    },
    "manufacturing": {
        "production", "assembly", "manufacturing", "warehouse", "forklift",
        "machine", "operator", "technician", "industrial", "plant",
        "fabrication", "quality", "maintenance",
    },
    "food_service": {
        "cook", "kitchen", "restaurant", "food", "server", "cashier",
        "fast food", "crew member", "barista", "prep", "dishwasher",
        "catering", "dining",
    },
    "government": {
        "government", "city", "state", "county", "federal", "municipal",
        "public", "civil", "administration", "clerk", "department",
    },
    "retail": {
        "retail", "store", "sales", "customer service", "cashier",
        "stocker", "merchandise", "team member", "associate", "shopping",
    },
    "construction": {
        "construction", "building", "carpenter", "electrician", "plumber",
        "hvac", "roofing", "concrete", "landscaping", "painter", "labor",
    },
    "transportation": {
        "driver", "delivery", "trucking", "cdl", "bus", "transport",
        "logistics", "shipping", "freight", "courier", "dispatch",
    },
}

SCHEDULE_CONFLICT_KEYWORDS: dict[str, set[str]] = {
    "daytime": {
        "night shift", "overnight", "11pm", "10pm", "graveyard",
        "third shift", "night",
    },
    "evening": {
        "morning", "day shift", "7am", "6am", "8am",
        "first shift", "early morning",
    },
    "night": {
        "day shift", "morning", "8am", "9am",
        "first shift", "daytime",
    },
}

SUNDAY_KEYWORDS: set[str] = {"sunday", "sundays", "weekend", "7 days"}

SKILLS_STOP_WORDS: set[str] = {
    "the", "and", "for", "with", "was", "had", "has", "have",
    "been", "were", "are", "did", "does", "will", "would",
    "could", "should", "may", "might", "shall", "can",
    "this", "that", "these", "those", "from", "into",
    "about", "over", "after", "before", "between", "under",
    "also", "just", "very", "some", "any", "all", "each",
    "year", "years", "month", "months", "work", "worked",
    "job", "jobs", "experience", "experienced",
}
