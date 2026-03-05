from pydantic import BaseModel, Field


class SimpleCreditRequest(BaseModel):
    """Flat fields for /v1/assess/simple — no score_band or AccountSummary needed."""
    credit_score: int = Field(..., ge=300, le=850)
    utilization_percent: float = Field(..., ge=0.0, le=100.0)
    total_accounts: int = Field(..., ge=0)
    open_accounts: int = Field(..., ge=0)
    negative_items: list[str] = Field(default_factory=list, max_length=50)
    payment_history_percent: float = Field(..., ge=0.0, le=100.0)
    oldest_account_months: int = Field(..., ge=0)
    total_balance: float = Field(0.0, ge=0)
    total_credit_limit: float = Field(0.0, ge=0)
    monthly_payments: float = Field(0.0, ge=0)


class CreditAssessmentResult(BaseModel):
    """Matches the actual /v1/assess response shape from the credit API.
    Uses dicts for nested structures -- the credit API owns these contracts."""
    barrier_severity: str
    barrier_details: list[dict]
    readiness: dict       # {score, fico_score, score_band, factors: {payment_history, utilization, ...}}
    thresholds: list[dict] # [{threshold_name, threshold_score, estimated_days, already_met, confidence}]
    dispute_pathway: dict  # {steps: [{step_number, action, description, ...}], total_estimated_days, statutes_cited}
    eligibility: list[dict] # [{product_name, category, required_score, status, gap_points, estimated_days_to_eligible}]
    disclaimer: str
