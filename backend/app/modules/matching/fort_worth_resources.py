"""Fort Worth resources -- barrier actions, career center, cert bodies, affinity."""

from app.modules.matching.career_center_types import CareerCenterInfo
from app.modules.matching.types import BarrierType

CAREER_CENTER = CareerCenterInfo(
    name="Workforce Solutions for Tarrant County",
    phone="817-413-4400",
    address="1200 Circle Dr, Fort Worth, TX 76119",
    hours="Mon-Fri 8am-5pm",
    transit_route="Trinity Metro Route 2, Lancaster Ave",
)

BARRIER_ACTIONS: dict[BarrierType, list[str]] = {
    BarrierType.CREDIT: [
        "Request free credit report from annualcreditreport.com",
        "Review report for errors and dispute inaccuracies",
        "Contact Workforce Solutions for financial counseling referral",
    ],
    BarrierType.TRANSPORTATION: [
        "Review Trinity Metro routes and schedules (Mon-Sat, ~5am-10pm)",
        "Apply for Trinity Metro reduced fare if income-eligible",
        "Contact Workforce Solutions about transportation assistance",
    ],
    BarrierType.CHILDCARE: [
        "Contact TWC Child Care Services for subsidy eligibility",
        "Research Texas Rising Star childcare providers near home and work",
        "Apply for Texas Pre-K or Head Start if age-eligible",
    ],
    BarrierType.HOUSING: [
        "Contact Fort Worth Housing Solutions for assistance programs",
        "Visit Tarrant County 211 for emergency housing resources",
        "Gather documentation for housing applications",
    ],
    BarrierType.HEALTH: [
        "Enroll in Medicaid if income-eligible (limited adult coverage)",
        "Contact JPS Health Network for sliding-scale services",
        "Schedule wellness check at a community health center",
    ],
    BarrierType.TRAINING: [
        "Review current certifications and identify expired credentials",
        "Contact Tarrant County College for training program enrollment",
        "Research financial aid and scholarship opportunities through TWC",
    ],
    BarrierType.CRIMINAL_RECORD: [
        "Request background check to understand what employers see",
        "Contact Legal Aid of NorthWest Texas for record clearing eligibility",
        "Connect with Tarrant County re-entry support programs",
    ],
}

CERT_DB = {
    "CNA": {
        "renewal_body": {
            "name": "Texas Board of Nursing",
            "phone": "512-305-7400",
        },
        "training_program": {
            "name": "Tarrant County College",
            "program": "Healthcare Certification Program",
        },
        "estimated_days": 45,
        "steps": [
            "Call Texas Board of Nursing (512-305-7400) to verify license status",
            "Complete reinstatement application and pay fees",
            "Enroll in Tarrant County College Healthcare Certification program",
            "Complete required clinical hours",
            "Submit documentation to Board for reinstatement",
        ],
    },
    "CDL": {
        "renewal_body": {
            "name": "Texas Department of Public Safety",
            "phone": "512-424-2000",
        },
        "training_program": {
            "name": "Tarrant County College",
            "program": "CDL Training Program",
        },
        "estimated_days": 30,
        "steps": [
            "Visit Texas DPS for license status check",
            "Complete DOT physical examination",
            "Enroll in Tarrant County College CDL program if needed",
            "Pass CDL knowledge and skills tests",
            "Submit renewal application to TX DPS",
        ],
    },
    "LPN": {
        "renewal_body": {
            "name": "Texas Board of Nursing",
            "phone": "512-305-7400",
        },
        "training_program": {
            "name": "Tarrant County College",
            "program": "Vocational Nursing Program",
        },
        "estimated_days": 60,
        "steps": [
            "Contact Texas Board of Nursing for reinstatement requirements",
            "Complete continuing education hours",
            "Enroll in TCC refresher if license lapsed > 2 years",
            "Submit reinstatement application with fees",
        ],
    },
}

RESOURCE_AFFINITY: dict[str, BarrierType] = {
    "trinity metro": BarrierType.TRANSPORTATION,
    "trinity": BarrierType.TRANSPORTATION,
    "hhsc": BarrierType.CHILDCARE,
    "health and human services": BarrierType.CHILDCARE,
    "childcare": BarrierType.CHILDCARE,
    "credit": BarrierType.CREDIT,
    "workforce solutions": BarrierType.TRAINING,
    "tarrant county college": BarrierType.TRAINING,
    "workforce training": BarrierType.TRAINING,
    "legal aid": BarrierType.CRIMINAL_RECORD,
    "re-entry": BarrierType.CRIMINAL_RECORD,
    "reentry": BarrierType.CRIMINAL_RECORD,
    "expunction": BarrierType.CRIMINAL_RECORD,
    "nondisclosure": BarrierType.CRIMINAL_RECORD,
}

FREE_CREDIT_RESOURCES = [
    "AnnualCreditReport.com: free weekly reports",
    "Consumer Financial Protection Bureau (CFPB)",
    "Legal Aid of NorthWest Texas: free credit dispute assistance",
]

CAREER_CENTER_STEP = (
    f"{CAREER_CENTER.name}, {CAREER_CENTER.phone}, {CAREER_CENTER.address}"
)
