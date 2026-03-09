"""Phase generators for criminal record and credit repair actions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.modules.plan.types import ActionCategory, ActionItem

if TYPE_CHECKING:
    from app.modules.matching.types import BarrierCard


def generate_criminal_actions(barriers: list[BarrierCard]) -> list[tuple[str, ActionItem]]:
    """Criminal record actions — phase depends on expungement eligibility timeline."""
    from app.modules.criminal.expungement import ExpungementEligibility
    from app.modules.matching.types import BarrierType

    results: list[tuple[str, ActionItem]] = []
    for card in barriers:
        if card.type != BarrierType.CRIMINAL_RECORD:
            continue
        if card.expungement is None:
            results.append(_legal_aid_action())
            continue
        action = _expungement_action(card.expungement, ExpungementEligibility)
        if action:
            results.append(action)
    return results


def _legal_aid_action() -> tuple[str, ActionItem]:
    return ("week_1_2", ActionItem(
        category=ActionCategory.CRIMINAL_RECORD,
        title="Contact Legal Services Alabama for record review",
        detail="Free consultation: 1-866-456-4995",
        priority=0,
        source_module="criminal_record",
        resource_name="Legal Services Alabama",
        resource_phone="1-866-456-4995",
    ))


def _expungement_action(exp, elig_enum) -> tuple[str, ActionItem] | None:
    if exp.eligibility == elig_enum.ELIGIBLE_NOW:
        return ("month_1", ActionItem(
            category=ActionCategory.CRIMINAL_RECORD,
            title="File expungement petition",
            detail=f"Filing fee: {exp.filing_fee or '$300'} (waivable)",
            priority=0,
            source_module="criminal_record",
        ))
    if exp.eligibility == elig_enum.ELIGIBLE_FUTURE:
        years = exp.years_remaining or 0
        phase = "month_3_6" if years <= 1 else "month_6_12"
        label = f"year{'s' if years != 1 else ''}"
        return (phase, ActionItem(
            category=ActionCategory.CRIMINAL_RECORD,
            title=f"Prepare for expungement filing (eligible in ~{years} {label})",
            detail=exp.notes,
            priority=0,
            source_module="criminal_record",
        ))
    return None


def generate_credit_actions(credit_result: dict | None) -> list[tuple[str, ActionItem]]:
    """Credit repair actions distributed across Month 1 and Month 2-3."""
    if not credit_result:
        return []
    severity = credit_result.get("barrier_severity", "")
    fico = _extract_fico(credit_result)

    if severity in ("moderate", "severe", "high"):
        return _moderate_credit_actions(fico, severity)
    if severity:
        return [("month_1", ActionItem(
            category=ActionCategory.CREDIT_REPAIR,
            title="Review credit report for errors",
            detail=f"Current FICO: {fico}" if fico else None,
            priority=0, source_module="credit",
        ))]
    return []


def _extract_fico(credit_result: dict) -> int | None:
    readiness = credit_result.get("readiness")
    return readiness.get("fico_score") if isinstance(readiness, dict) else None


def _moderate_credit_actions(fico, severity) -> list[tuple[str, ActionItem]]:
    return [
        ("month_1", ActionItem(
            category=ActionCategory.CREDIT_REPAIR,
            title="Request free credit reports from annualcreditreport.com",
            detail=f"Current FICO: {fico}" if fico else None,
            priority=0, source_module="credit",
        )),
        ("month_1", ActionItem(
            category=ActionCategory.CREDIT_REPAIR,
            title="Call GreenPath Financial Wellness for free counseling",
            detail="1-800-550-1961",
            priority=1, source_module="credit",
            resource_name="GreenPath Financial Wellness",
            resource_phone="1-800-550-1961",
        )),
        ("month_2_3", ActionItem(
            category=ActionCategory.CREDIT_REPAIR,
            title="Follow up on credit disputes (30-day response window)",
            priority=0, source_module="credit",
        )),
    ]
