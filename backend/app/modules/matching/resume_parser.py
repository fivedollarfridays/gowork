"""Resume text parsing: extract skills, industries, and certifications."""

import re

from pydantic import BaseModel

from app.modules.matching.job_keywords import INDUSTRY_KEYWORDS


class ParsedResume(BaseModel):
    """Structured result from resume text parsing."""

    skills: list[str] = []
    industries: list[str] = []
    certifications: list[str] = []
    experience_keywords: list[str] = []
    word_count: int = 0


# Certifications to detect (uppercase canonical form)
_CERT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("CNA", re.compile(r"\bCNA\b", re.IGNORECASE)),
    ("CDL", re.compile(r"\bCDL\b", re.IGNORECASE)),
    ("LPN", re.compile(r"\bLPN\b", re.IGNORECASE)),
    ("GED", re.compile(r"\bGED\b", re.IGNORECASE)),
]

# Common job titles to detect in experience sections
_EXPERIENCE_KEYWORDS: set[str] = {
    "cashier", "nurse", "driver", "warehouse", "cook",
    "server", "custodian", "mechanic", "electrician",
    "plumber", "caregiver", "aide", "technician",
    "operator", "clerk", "stocker", "security",
}


def _extract_skills(text: str) -> list[str]:
    """Match tokens against INDUSTRY_KEYWORDS values."""
    if not text.strip():
        return []

    text_lower = text.lower()
    found: list[str] = []

    for keywords in INDUSTRY_KEYWORDS.values():
        for keyword in keywords:
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, text_lower):
                if keyword not in found:
                    found.append(keyword)

    return found


def _detect_industries(skills: list[str]) -> list[str]:
    """Reverse-map matched skill keywords to industry categories."""
    if not skills:
        return []

    industries: list[str] = []
    skills_set = set(skills)

    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if skills_set & keywords:
            industries.append(industry)

    return industries


def _detect_certifications(text: str) -> list[str]:
    """Detect certifications via regex with word boundaries."""
    if not text.strip():
        return []

    found: list[str] = []
    for cert_name, pattern in _CERT_PATTERNS:
        if pattern.search(text):
            found.append(cert_name)

    return found


def _extract_experience(text: str) -> list[str]:
    """Detect job title keywords in resume text."""
    if not text.strip():
        return []

    text_lower = text.lower()
    found: list[str] = []

    for keyword in _EXPERIENCE_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            found.append(keyword)

    return found


def parse_resume(text: str) -> ParsedResume:
    """Parse resume text into structured skills, industries, and certs."""
    words = text.split()
    word_count = len(words)

    if not text.strip():
        return ParsedResume(word_count=0)

    skills = _extract_skills(text)
    industries = _detect_industries(skills)
    certifications = _detect_certifications(text)
    experience = _extract_experience(text)

    return ParsedResume(
        skills=skills,
        industries=industries,
        certifications=certifications,
        experience_keywords=experience,
        word_count=word_count,
    )
