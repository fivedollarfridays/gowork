"""Per-program application data — Montgomery/Alabama offices, URLs, contacts."""

from app.modules.benefits.types import ProgramApplicationInfo

APPLICATION_DATA: dict[str, ProgramApplicationInfo] = {
    "SNAP": ProgramApplicationInfo(
        application_url="https://mydhr.alabama.gov",
        application_steps=[
            "Create an account at mydhr.alabama.gov",
            "Complete the online application for Food Assistance",
            "Upload proof of income, ID, and residency",
            "Attend a phone or in-person interview with DHR",
        ],
        required_documents=[
            "Government-issued photo ID",
            "Proof of income (pay stubs, employer letter)",
            "Proof of residency (utility bill, lease)",
            "Social Security numbers for all household members",
        ],
        office_name="Montgomery County DHR",
        office_address="1050 Government St, Montgomery, AL 36104",
        office_phone="(334) 293-3100",
        processing_time="30 days from completed application",
    ),
    "TANF": ProgramApplicationInfo(
        application_url="https://mydhr.alabama.gov",
        application_steps=[
            "Apply online at mydhr.alabama.gov or in person at DHR",
            "Complete Family Assistance application",
            "Provide proof of income and work activity",
            "Attend required orientation session",
        ],
        required_documents=[
            "Government-issued photo ID",
            "Proof of income (pay stubs, employer letter)",
            "Birth certificates for dependent children",
            "Proof of work activity or job search",
            "Social Security numbers for all household members",
        ],
        office_name="Montgomery County DHR",
        office_address="1050 Government St, Montgomery, AL 36104",
        office_phone="(334) 293-3100",
        processing_time="30-45 days from completed application",
    ),
    "Medicaid": ProgramApplicationInfo(
        application_url="https://www.medicaid.alabama.gov",
        application_steps=[
            "Alabama has not expanded Medicaid for most adults",
            "Check if you qualify under limited categories (pregnant, disabled)",
            "Contact a benefits navigator for alternative coverage options",
            "Explore Healthcare.gov marketplace plans",
        ],
        required_documents=[
            "Government-issued photo ID",
            "Proof of income",
            "Proof of residency",
            "Documentation of qualifying condition (if applicable)",
        ],
        office_name="Alabama Medicaid Agency — Montgomery",
        office_address="501 Dexter Ave, Montgomery, AL 36104",
        office_phone="(334) 242-5000",
        processing_time="45 days; limited adult eligibility in Alabama",
    ),
    "ALL_Kids": ProgramApplicationInfo(
        application_url="https://www.medicaid.alabama.gov/content/4.0_Programs/4.2_ALL_Kids.aspx",
        application_steps=[
            "Download or request an ALL Kids application",
            "Complete and mail the application with required documents",
            "Or apply in person at your local Medicaid office",
            "Coverage begins once approved — retroactive to application date",
        ],
        required_documents=[
            "Birth certificates for children being enrolled",
            "Proof of household income (pay stubs, tax return)",
            "Proof of Alabama residency",
            "Social Security numbers for children",
        ],
        office_name="Alabama Medicaid Agency — Montgomery",
        office_address="501 Dexter Ave, Montgomery, AL 36104",
        office_phone="(334) 242-5000",
        processing_time="45 days from completed application",
    ),
    "Childcare_Subsidy": ProgramApplicationInfo(
        application_url="https://mydhr.alabama.gov",
        application_steps=[
            "Apply through DHR for Child Care Assistance",
            "Provide proof of employment or training enrollment",
            "Select an approved childcare provider",
            "DHR determines copay based on household income",
        ],
        required_documents=[
            "Proof of employment or training enrollment",
            "Proof of household income",
            "Child's birth certificate",
            "Selected childcare provider information",
            "Government-issued photo ID",
        ],
        office_name="Montgomery County DHR — Childcare Unit",
        office_address="1050 Government St, Montgomery, AL 36104",
        office_phone="(334) 293-3100",
        processing_time="30 days; provider must be DHR-approved",
    ),
    "Section_8": ProgramApplicationInfo(
        application_url="https://www.mhatoday.org",
        application_steps=[
            "Check if the Montgomery Housing Authority waitlist is open",
            "Submit a pre-application when the waitlist opens",
            "Wait for your name to be called (typical wait: 2-3 years)",
            "Complete full application and provide required documents",
            "Attend a briefing session and search for approved housing",
        ],
        required_documents=[
            "Government-issued photo ID for all adults",
            "Birth certificates for all household members",
            "Proof of income (pay stubs, benefits letters)",
            "Social Security numbers for all household members",
            "Rental history for the past 3 years",
        ],
        office_name="Montgomery Housing Authority",
        office_address="525 S Lawrence St, Montgomery, AL 36104",
        office_phone="(334) 262-4471",
        processing_time="Waitlist typically 2-3 years; apply when open",
    ),
    "LIHEAP": ProgramApplicationInfo(
        application_url="https://mydhr.alabama.gov",
        application_steps=[
            "Apply at DHR during the heating season (October-March)",
            "Provide proof of income and most recent utility bill",
            "DHR determines benefit amount based on household need",
            "Payment is sent directly to your utility provider",
        ],
        required_documents=[
            "Most recent utility bill (in applicant's name)",
            "Proof of household income",
            "Government-issued photo ID",
            "Social Security numbers for all household members",
        ],
        office_name="Montgomery County DHR — Energy Assistance",
        office_address="1050 Government St, Montgomery, AL 36104",
        office_phone="(334) 293-3100",
        processing_time="Seasonal program (October-March); 2-4 weeks when open",
    ),
}


def get_application_info(program: str) -> ProgramApplicationInfo | None:
    """Look up application info for a program, or None if unknown."""
    return APPLICATION_DATA.get(program)
