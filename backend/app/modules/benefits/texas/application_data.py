"""Per-program application data -- Fort Worth/Texas offices, URLs, contacts."""

from app.modules.benefits.types import ProgramApplicationInfo

APPLICATION_DATA: dict[str, ProgramApplicationInfo] = {
    "SNAP": ProgramApplicationInfo(
        application_url="https://www.yourtexasbenefits.com",
        application_steps=[
            "Create an account at yourtexasbenefits.com",
            "Complete the online application for SNAP Food Benefits",
            "Upload proof of income, ID, and residency",
            "Attend a phone or in-person interview with HHSC",
        ],
        required_documents=[
            "Government-issued photo ID",
            "Proof of income (pay stubs, employer letter)",
            "Proof of Texas residency (utility bill, lease)",
            "Social Security numbers for all household members",
        ],
        office_name="Tarrant County HHSC Office",
        office_address="3636 W Seminary Dr, Fort Worth, TX 76115",
        office_phone="(817) 255-3700",
        processing_time="30 days from completed application",
    ),
    "TANF": ProgramApplicationInfo(
        application_url="https://www.yourtexasbenefits.com",
        application_steps=[
            "Apply online at yourtexasbenefits.com or visit HHSC office",
            "Complete the TANF Cash Assistance application",
            "Provide proof of income and work activity",
            "Attend required orientation session",
        ],
        required_documents=[
            "Government-issued photo ID",
            "Proof of income (pay stubs, employer letter)",
            "Birth certificates for dependent children",
            "Proof of work search or work activity",
            "Social Security numbers for all household members",
        ],
        office_name="Tarrant County HHSC Office",
        office_address="3636 W Seminary Dr, Fort Worth, TX 76115",
        office_phone="(817) 255-3700",
        processing_time="30-45 days from completed application",
    ),
    "Medicaid": ProgramApplicationInfo(
        application_url="https://www.yourtexasbenefits.com",
        application_steps=[
            "Texas has not expanded Medicaid for most adults",
            "Check if you qualify under limited categories (pregnant, disabled, elderly)",
            "Contact a benefits navigator for alternative coverage options",
            "Explore Healthcare.gov marketplace plans",
        ],
        required_documents=[
            "Government-issued photo ID",
            "Proof of income",
            "Proof of Texas residency",
            "Documentation of qualifying condition (if applicable)",
        ],
        office_name="Tarrant County HHSC Office",
        office_address="3636 W Seminary Dr, Fort Worth, TX 76115",
        office_phone="(817) 255-3700",
        processing_time="45 days; limited adult eligibility in Texas",
    ),
    "CHIP": ProgramApplicationInfo(
        application_url="https://www.yourtexasbenefits.com",
        application_steps=[
            "Apply online at yourtexasbenefits.com for children's coverage",
            "Complete the CHIP application with household income details",
            "Or call 2-1-1 for help applying by phone",
            "Coverage begins once approved (may be retroactive to application date)",
        ],
        required_documents=[
            "Birth certificates for children being enrolled",
            "Proof of household income (pay stubs, tax return)",
            "Proof of Texas residency",
            "Social Security numbers for children",
        ],
        office_name="Tarrant County HHSC Office",
        office_address="3636 W Seminary Dr, Fort Worth, TX 76115",
        office_phone="(817) 255-3700",
        processing_time="45 days from completed application",
    ),
    "Childcare_Subsidy": ProgramApplicationInfo(
        application_url="https://www.twc.texas.gov/programs/child-care-services",
        application_steps=[
            "Contact Workforce Solutions for Tarrant County",
            "Apply for Child Care Services through TWC",
            "Provide proof of employment or training enrollment",
            "Select a Texas Rising Star childcare provider",
        ],
        required_documents=[
            "Proof of employment or training enrollment",
            "Proof of household income",
            "Child's birth certificate",
            "Selected childcare provider information",
            "Government-issued photo ID",
        ],
        office_name="Workforce Solutions for Tarrant County",
        office_address="1200 Circle Dr, Fort Worth, TX 76119",
        office_phone="(817) 413-4400",
        processing_time="30 days; provider must be TWC-approved",
    ),
    "Section_8": ProgramApplicationInfo(
        application_url="https://www.fwhs.org",
        application_steps=[
            "Check if Fort Worth Housing Solutions waitlist is open",
            "Submit a pre-application when the waitlist opens",
            "Wait for your name to be called (typical wait: 1-3 years)",
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
        office_name="Fort Worth Housing Solutions",
        office_address="1201 E 13th St, Fort Worth, TX 76102",
        office_phone="(817) 333-3400",
        processing_time="Waitlist typically 1-3 years; apply when open",
    ),
    "CEAP": ProgramApplicationInfo(
        application_url="https://www.capunited.org",
        application_steps=[
            "Contact Community Action Partners of Tarrant County",
            "Apply for CEAP during the enrollment period",
            "Provide proof of income and most recent utility bill",
            "CEAP determines benefit amount based on household need",
        ],
        required_documents=[
            "Most recent utility bill (in applicant's name)",
            "Proof of household income",
            "Government-issued photo ID",
            "Social Security numbers for all household members",
        ],
        office_name="Community Action Partners of Tarrant County",
        office_address="1600 Campus Dr, Fort Worth, TX 76119",
        office_phone="(817) 531-7300",
        processing_time="Seasonal program; 2-4 weeks when open",
    ),
}


def get_application_info(program: str) -> ProgramApplicationInfo | None:
    """Look up application info for a TX program, or None if unknown."""
    return APPLICATION_DATA.get(program)
