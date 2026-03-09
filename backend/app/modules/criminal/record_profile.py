"""Criminal record profile models — structured charge-type data.

Expands the boolean criminal_record barrier into a detailed profile
with record types, charge categories, years since conviction, and
sentence completion status. All fields are optional with safe defaults.
"""

from enum import Enum

from pydantic import BaseModel, Field


class RecordType(str, Enum):
    """Types of criminal record entries."""

    FELONY = "felony"
    MISDEMEANOR = "misdemeanor"
    ARREST_ONLY = "arrest_only"
    EXPUNGED = "expunged"


class ChargeCategory(str, Enum):
    """Broad charge categories for employer policy matching."""

    VIOLENCE = "violence"
    THEFT = "theft"
    DRUG = "drug"
    DUI = "dui"
    SEX_OFFENSE = "sex_offense"
    FRAUD = "fraud"
    OTHER = "other"


class RecordProfile(BaseModel):
    """Structured criminal record profile — all fields optional."""

    record_types: list[RecordType] = Field(default_factory=list)
    charge_categories: list[ChargeCategory] = Field(default_factory=list)
    years_since_conviction: int | None = None
    completed_sentence: bool = False
