"""Criminal record job filter — enriches jobs with record eligibility status."""

from app.modules.criminal.employer_policy import EmployerPolicy, matches_record
from app.modules.criminal.record_profile import RecordProfile


def _find_policy(company: str | None, policies: list[EmployerPolicy]) -> EmployerPolicy | None:
    """Find employer policy matching job company name (case-insensitive prefix)."""
    if not company:
        return None
    company_lower = company.lower()
    for policy in policies:
        if policy.employer_name.lower() in company_lower or company_lower in policy.employer_name.lower():
            return policy
    return None


_DEFAULT_RECORD_FIELDS = {
    "fair_chance": False,
    "record_eligible": True,
    "background_check_timing": None,
    "record_note": None,
}


def _passthrough_with_source_fair_chance(enriched: dict) -> dict:
    """Apply default record fields but PRESERVE the seed-data fair_chance.

    The honestjobs seed loader stores fair_chance as SQLite INTEGER (0/1);
    spreading the defaults dict last would clobber that signal to ``False``
    for every user who lacks a RecordProfile (criminal_record barrier
    checked, optional form blank — i.e. the Carlos demo path).
    """
    return {
        **enriched,
        **_DEFAULT_RECORD_FIELDS,
        "fair_chance": bool(enriched.get("fair_chance", False)),
    }


def enrich_job_with_record_status(
    job: dict,
    profile: RecordProfile | None,
    policies: list[EmployerPolicy],
) -> dict:
    """Add fair_chance, record_eligible, background_check_timing, record_note to job."""
    enriched = dict(job)

    if profile is None:
        return _passthrough_with_source_fair_chance(enriched)

    policy = _find_policy(job.get("company"), policies)

    if policy is None:
        return _passthrough_with_source_fair_chance(enriched)

    eligible = matches_record(policy, profile)
    enriched["fair_chance"] = policy.fair_chance and eligible
    enriched["record_eligible"] = eligible
    enriched["background_check_timing"] = policy.background_check_timing
    enriched["record_note"] = _build_record_note(policy, profile, eligible)
    return enriched


def _build_record_note(
    policy: EmployerPolicy,
    profile: RecordProfile,
    eligible: bool,
) -> str | None:
    """Generate a user-facing note about record eligibility."""
    if eligible:
        return None
    if (
        policy.lookback_years is not None
        and profile.years_since_conviction is not None
        and profile.years_since_conviction < policy.lookback_years
    ):
        wait = policy.lookback_years - profile.years_since_conviction
        return f"Eligible after {wait} more year{'s' if wait != 1 else ''}"
    return "Not eligible based on charge type"


def filter_jobs_by_record(
    jobs: list[dict],
    profile: RecordProfile | None,
    policies: list[EmployerPolicy],
) -> list[dict]:
    """Enrich all jobs with record status, sort fair-chance first."""
    enriched = [enrich_job_with_record_status(j, profile, policies) for j in jobs]
    enriched.sort(key=lambda j: (not j["fair_chance"], not j["record_eligible"]))
    return enriched
