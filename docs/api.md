# MontGoWork API Reference

Base URL: `http://localhost:8000`

---

## Endpoints Overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root health check |
| GET | `/health` | Detailed health status with version |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe (database connectivity) |
| POST | `/api/assessment/` | Submit barrier assessment and generate a re-entry plan |
| GET | `/api/plan/{session_id}` | Retrieve an existing session plan |
| POST | `/api/plan/{session_id}/generate` | Generate AI narrative for an existing plan |
| POST | `/api/credit/assess` | Proxy credit assessment to the credit microservice |
| GET | `/api/jobs/` | List job listings with optional filters |
| GET | `/api/jobs/{job_id}` | Get a single job listing by ID |
| POST | `/api/brightdata/crawl` | Trigger a BrightData web crawl |
| GET | `/api/brightdata/status/{snapshot_id}` | Check crawl status and retrieve results |
| POST | `/api/brightdata/precrawl` | Admin: pre-populate Montgomery job listings |

---

## Root

### GET /

Root health check. Returns a simple status message.

**Response** `200 OK`

```json
{
  "message": "MontGoWork API",
  "status": "running"
}
```

**curl**

```bash
curl http://localhost:8000/
```

---

## Health

### GET /health

Detailed health status including version and uptime.

**Response** `200 OK`

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3421.7
}
```

The `status` field is one of: `healthy`, `degraded`, `unhealthy`.

**curl**

```bash
curl http://localhost:8000/health
```

---

### GET /health/live

Liveness probe. Returns whether the application process is running.

**Response** `200 OK`

```json
{
  "alive": true,
  "uptime_seconds": 3421.7
}
```

**curl**

```bash
curl http://localhost:8000/health/live
```

---

### GET /health/ready

Readiness probe. Checks whether the application can serve traffic (database connectivity).

**Response** `200 OK` (ready) or `503 Service Unavailable` (not ready)

```json
{
  "ready": true,
  "checks": [
    {
      "name": "database",
      "status": "up",
      "latency_ms": 2.4,
      "error": null
    }
  ]
}
```

Each check has `status` of `up`, `down`, or `unknown`.

**curl**

```bash
curl http://localhost:8000/health/ready
```

---

## Assessment

### POST /api/assessment/

Submit a barrier assessment form. Creates a new session, builds a user profile, runs the matching engine, and returns a complete re-entry plan.

**Request Body**

```json
{
  "zip_code": "36104",
  "employment_status": "unemployed",
  "barriers": {
    "credit": true,
    "transportation": true,
    "childcare": false,
    "housing": false,
    "health": false,
    "training": false,
    "criminal_record": false
  },
  "work_history": "3 years warehouse experience, forklift certified",
  "target_industries": ["warehouse", "logistics"],
  "has_vehicle": false,
  "schedule_constraints": {
    "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "available_hours": "daytime"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `zip_code` | string | Yes | Montgomery area zip code. Must match pattern `361xx`. |
| `employment_status` | string | Yes | One of: `unemployed`, `underemployed`, `seeking_change`. |
| `barriers` | object | Yes | Map of barrier types to boolean. Keys: `credit`, `transportation`, `childcare`, `housing`, `health`, `training`, `criminal_record`. |
| `work_history` | string | Yes | Free-text work history. Max 500 characters. |
| `target_industries` | string[] | No | Target industry names. Defaults to empty list. |
| `has_vehicle` | boolean | No | Whether the resident has a vehicle. Defaults to `false`. |
| `schedule_constraints` | object | No | Schedule availability. Defaults to weekday daytime. |
| `schedule_constraints.available_days` | string[] | No | Days available. Defaults to Monday through Friday. |
| `schedule_constraints.available_hours` | string | No | One of: `daytime`, `evening`, `night`, `flexible`. Defaults to `daytime`. |

**Response** `200 OK`

```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "profile": {
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "zip_code": "36104",
    "employment_status": "unemployed",
    "barrier_count": 2,
    "primary_barriers": ["credit", "transportation"],
    "barrier_severity": "medium",
    "needs_credit_assessment": true,
    "transit_dependent": true,
    "schedule_type": "daytime",
    "work_history": "3 years warehouse experience, forklift certified",
    "target_industries": ["warehouse", "logistics"]
  },
  "plan": {
    "plan_id": "plan-uuid",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "resident_summary": null,
    "barriers": [
      {
        "type": "credit",
        "severity": "medium",
        "title": "Credit Barrier",
        "timeline_days": 90,
        "actions": ["Review credit report", "Dispute errors"],
        "resources": [
          {
            "id": 1,
            "name": "Consumer Credit Counseling",
            "category": "social_service",
            "subcategory": null,
            "address": "123 Main St, Montgomery, AL",
            "phone": "334-555-0100",
            "url": null,
            "eligibility": null,
            "services": ["credit counseling", "debt management"],
            "notes": null
          }
        ],
        "transit_matches": []
      }
    ],
    "job_matches": [
      {
        "title": "Warehouse Associate",
        "company": "Montgomery Logistics",
        "location": "Montgomery, AL",
        "url": "https://example.com/apply",
        "source": "indeed",
        "transit_accessible": true,
        "route": "Route 7",
        "credit_check_required": "no",
        "eligible_now": true,
        "eligible_after": null
      }
    ],
    "immediate_next_steps": [
      "Visit Consumer Credit Counseling at 123 Main St",
      "Apply to Warehouse Associate at Montgomery Logistics"
    ],
    "credit_readiness_score": null,
    "eligible_now": ["Warehouse Associate"],
    "eligible_after_repair": ["Bank Teller"]
  }
}
```

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | Assessment created and plan generated |
| 422 | Validation error (invalid zip code, missing required fields, etc.) |

**curl**

```bash
curl -X POST http://localhost:8000/api/assessment/ \
  -H "Content-Type: application/json" \
  -d '{
    "zip_code": "36104",
    "employment_status": "unemployed",
    "barriers": {
      "credit": true,
      "transportation": true,
      "childcare": false,
      "housing": false,
      "health": false,
      "training": false,
      "criminal_record": false
    },
    "work_history": "3 years warehouse experience, forklift certified",
    "target_industries": ["warehouse", "logistics"],
    "has_vehicle": false,
    "schedule_constraints": {
      "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "available_hours": "daytime"
    }
  }'
```

---

## Plan

### GET /api/plan/{session_id}

Retrieve an existing session plan by session ID.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | UUID of the session created during assessment. |

**Response** `200 OK`

```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "barriers": ["credit", "transportation"],
  "qualifications": "3 years warehouse experience, forklift certified",
  "plan": {
    "plan_id": "plan-uuid",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "resident_summary": null,
    "barriers": [],
    "job_matches": [],
    "immediate_next_steps": [],
    "credit_readiness_score": null,
    "eligible_now": [],
    "eligible_after_repair": []
  }
}
```

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | Session found and plan returned |
| 404 | Session not found |
| 500 | Corrupt session data (JSON decode error) |

**curl**

```bash
curl http://localhost:8000/api/plan/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

### POST /api/plan/{session_id}/generate

Generate an AI narrative for an existing plan. Uses the Claude API to produce a "Monday Morning" summary paragraph. Falls back to a template-based narrative if the Claude API is unavailable.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | UUID of the session. Must already have a plan from assessment. |

**Request Body**

None. The endpoint reads plan data from the database.

**Response** `200 OK`

```json
{
  "summary": "Monday morning, walk to the Route 7 bus stop at 7:15am. Take it downtown to Montgomery Logistics on Commerce St. Ask for the hiring manager and mention the warehouse associate position...",
  "key_actions": [
    "Get your credit report from annualcreditreport.com",
    "Visit Consumer Credit Counseling at 123 Main St",
    "Apply to Warehouse Associate at Montgomery Logistics",
    "Follow up with the employer within 5 business days"
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `summary` | string | AI-generated narrative paragraph describing the resident's next steps. |
| `key_actions` | string[] | Top 3-5 prioritized action items. |

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | Narrative generated (AI or fallback) |
| 400 | No plan exists for this session (run assessment first) |
| 404 | Session not found |
| 500 | Corrupt session data |

**curl**

```bash
curl -X POST http://localhost:8000/api/plan/a1b2c3d4-e5f6-7890-abcd-ef1234567890/generate
```

---

## Credit

### POST /api/credit/assess

Proxy endpoint to the credit assessment microservice. Sends credit profile data and returns a full assessment with barrier severity, readiness score, dispute pathway, and eligibility analysis.

**Request Body**

```json
{
  "credit_score": 580,
  "utilization_percent": 72.5,
  "total_accounts": 8,
  "open_accounts": 5,
  "negative_items": ["late_payment", "collection"],
  "payment_history_percent": 85.0,
  "oldest_account_months": 36,
  "total_balance": 12500.00,
  "total_credit_limit": 17000.00,
  "monthly_payments": 450.00
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `credit_score` | integer | Yes | FICO score. Range: 300-850. |
| `utilization_percent` | float | Yes | Credit utilization percentage. Range: 0-100. |
| `total_accounts` | integer | Yes | Total number of credit accounts. Min: 0. |
| `open_accounts` | integer | Yes | Number of open accounts. Min: 0. |
| `negative_items` | string[] | No | List of negative item types. Max 50 items. Defaults to empty. |
| `payment_history_percent` | float | Yes | On-time payment percentage. Range: 0-100. |
| `oldest_account_months` | integer | Yes | Age of oldest account in months. Min: 0. |
| `total_balance` | float | No | Total outstanding balance. Min: 0. Defaults to 0. |
| `total_credit_limit` | float | No | Total credit limit across accounts. Min: 0. Defaults to 0. |
| `monthly_payments` | float | No | Total monthly payment obligations. Min: 0. Defaults to 0. |

**Response** `200 OK`

```json
{
  "barrier_severity": "medium",
  "barrier_details": [
    {
      "factor": "utilization",
      "severity": "high",
      "description": "Credit utilization is 72.5%, well above the recommended 30%"
    }
  ],
  "readiness": {
    "score": 45,
    "fico_score": 580,
    "score_band": "fair",
    "factors": {
      "payment_history": 85.0,
      "utilization": 72.5,
      "account_age": 36,
      "negative_items": 2
    }
  },
  "thresholds": [
    {
      "threshold_name": "Fair Credit",
      "threshold_score": 620,
      "estimated_days": 90,
      "already_met": false,
      "confidence": 0.7
    }
  ],
  "dispute_pathway": {
    "steps": [
      {
        "step_number": 1,
        "action": "Obtain credit reports",
        "description": "Request free reports from all three bureaus"
      }
    ],
    "total_estimated_days": 120,
    "statutes_cited": ["FCRA Section 611"]
  },
  "eligibility": [
    {
      "product_name": "Secured Credit Card",
      "category": "credit_building",
      "required_score": 500,
      "status": "eligible",
      "gap_points": 0,
      "estimated_days_to_eligible": 0
    }
  ],
  "disclaimer": "This assessment is for educational purposes only and does not constitute financial advice."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `barrier_severity` | string | Overall credit barrier severity. |
| `barrier_details` | object[] | Per-factor barrier analysis. |
| `readiness` | object | Readiness score, FICO score, score band, and contributing factors. |
| `thresholds` | object[] | Credit score thresholds with estimated time to reach. |
| `dispute_pathway` | object | Step-by-step dispute process with timeline and statutes. |
| `eligibility` | object[] | Product eligibility status based on current credit profile. |
| `disclaimer` | string | Legal disclaimer. |

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | Credit assessment completed |
| 422 | Validation error (score out of range, missing fields, etc.) |
| 502 | Credit API returned an error or network error |
| 503 | Credit assessment service unavailable (not running) |
| 504 | Credit assessment service timed out |

**curl**

```bash
curl -X POST http://localhost:8000/api/credit/assess \
  -H "Content-Type: application/json" \
  -d '{
    "credit_score": 580,
    "utilization_percent": 72.5,
    "total_accounts": 8,
    "open_accounts": 5,
    "negative_items": ["late_payment", "collection"],
    "payment_history_percent": 85.0,
    "oldest_account_months": 36,
    "total_balance": 12500.00,
    "total_credit_limit": 17000.00,
    "monthly_payments": 450.00
  }'
```

---

## Jobs

### GET /api/jobs/

List job listings with optional barrier, transit, and industry filters. Jobs are enriched with industry classification, credit check requirements, transit accessibility, and application steps.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `barriers` | string | No | Comma-separated barrier types to filter by. Currently supports `credit` (excludes jobs requiring credit checks). Example: `credit,transportation`. |
| `transit_accessible` | boolean | No | If `true`, only return jobs with transit accessibility information. |
| `industry` | string | No | Filter by industry name (exact match). |

**Response** `200 OK`

```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Warehouse Associate",
      "company": "Montgomery Logistics",
      "location": "Montgomery, AL",
      "url": "https://example.com/apply",
      "industry": "logistics",
      "credit_check_required": "no",
      "transit_info": {
        "accessible": true,
        "routes": [
          {
            "route_number": 7,
            "route_name": "Eastern Blvd"
          }
        ],
        "schedule": "Mon-Sat, no Sunday service"
      },
      "application_steps": [
        "Apply online at https://example.com/apply",
        "Bring government-issued ID and Social Security card",
        "Follow up with Montgomery Logistics within 5 business days"
      ]
    }
  ],
  "total": 1
}
```

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | Job listings returned (may be empty) |

**curl**

```bash
# All jobs
curl 'http://localhost:8000/api/jobs/'

# Filter: exclude jobs requiring credit checks
curl 'http://localhost:8000/api/jobs/?barriers=credit'

# Filter: transit accessible only
curl 'http://localhost:8000/api/jobs/?transit_accessible=true'

# Filter: specific industry
curl 'http://localhost:8000/api/jobs/?industry=logistics'

# Combined filters
curl 'http://localhost:8000/api/jobs/?barriers=credit&transit_accessible=true&industry=logistics'
```

---

### GET /api/jobs/{job_id}

Get a single job listing by ID, enriched with transit info and application steps.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | integer | Database ID of the job listing. |

**Response** `200 OK`

```json
{
  "id": 1,
  "title": "Warehouse Associate",
  "company": "Montgomery Logistics",
  "location": "Montgomery, AL",
  "url": "https://example.com/apply",
  "industry": "logistics",
  "credit_check_required": "no",
  "transit_info": {
    "accessible": true,
    "routes": [
      {
        "route_number": 7,
        "route_name": "Eastern Blvd"
      }
    ],
    "schedule": "Mon-Sat, no Sunday service"
  },
  "application_steps": [
    "Apply online at https://example.com/apply",
    "Bring government-issued ID and Social Security card",
    "Follow up with Montgomery Logistics within 5 business days"
  ]
}
```

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | Job found and returned |
| 404 | Job not found |

**curl**

```bash
curl http://localhost:8000/api/jobs/1
```

---

## BrightData

### POST /api/brightdata/crawl

Trigger a BrightData web crawl for the given URLs. Returns a snapshot ID immediately; use the status endpoint to poll for results.

**Request Body**

```json
{
  "urls": [
    "https://www.indeed.com/jobs?q=&l=Montgomery%2C+AL&radius=25",
    "https://www.linkedin.com/jobs/search/?location=Montgomery%2C+Alabama"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `urls` | string[] | Yes | One or more URLs to crawl. Must contain at least one URL. |

**Response** `200 OK`

```json
{
  "snapshot_id": "snap_abc123def456",
  "status": "starting",
  "message": "Crawl triggered"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `snapshot_id` | string | Unique identifier for tracking this crawl job. |
| `status` | string | Initial status. One of: `starting`, `running`, `ready`, `failed`. |
| `message` | string | Human-readable status message. |

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | Crawl triggered successfully |
| 422 | Validation error (empty URLs list) |
| 502 | BrightData API error |
| 503 | BrightData integration not configured |

**curl**

```bash
curl -X POST http://localhost:8000/api/brightdata/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.indeed.com/jobs?q=&l=Montgomery%2C+AL&radius=25"
    ]
  }'
```

---

### GET /api/brightdata/status/{snapshot_id}

Check the status of a crawl job. When the crawl is complete, results are automatically cached to the database.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `snapshot_id` | string | Snapshot ID returned by the crawl trigger endpoint. |

**Response** `200 OK` (in progress)

```json
{
  "snapshot_id": "snap_abc123def456",
  "status": "running",
  "progress_pct": 45.0,
  "jobs_found": null,
  "message": "Crawl in progress"
}
```

**Response** `200 OK` (complete)

```json
{
  "snapshot_id": "snap_abc123def456",
  "status": "ready",
  "progress_pct": null,
  "jobs_found": 42,
  "message": "Crawl complete \u2014 42 jobs cached"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `snapshot_id` | string | The crawl job identifier. |
| `status` | string | One of: `starting`, `running`, `ready`, `failed`. |
| `progress_pct` | float or null | Completion percentage (0-100) while running. Null when complete. |
| `jobs_found` | integer or null | Number of jobs cached. Only populated when status is `ready`. |
| `message` | string | Human-readable status message. |

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | Status returned |
| 502 | BrightData API error |
| 503 | BrightData integration not configured |

**curl**

```bash
curl http://localhost:8000/api/brightdata/status/snap_abc123def456
```

---

### POST /api/brightdata/precrawl

Admin endpoint. Triggers a full crawl of Montgomery-area job sites (Indeed and LinkedIn), polls until complete, and caches all results. Skips if fresh data (less than 24 hours old) already exists.

**Request Body**

None.

**Response** `200 OK` (crawl executed)

```json
{
  "snapshot_id": "snap_abc123def456",
  "jobs_cached": 42,
  "skipped": false
}
```

**Response** `200 OK` (skipped, recent data exists)

```json
{
  "snapshot_id": null,
  "jobs_cached": 0,
  "skipped": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `snapshot_id` | string or null | Crawl snapshot ID, or null if skipped. |
| `jobs_cached` | integer | Number of jobs stored in the database. |
| `skipped` | boolean | True if crawl was skipped due to recent data. |

**Status Codes**

| Code | Description |
|------|-------------|
| 200 | Precrawl completed or skipped |
| 502 | BrightData API error during crawl or polling |
| 503 | BrightData integration not configured |

**curl**

```bash
curl -X POST http://localhost:8000/api/brightdata/precrawl
```

---

## Error Responses

All error responses follow the standard FastAPI error format:

```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (422), the response includes field-level details:

```json
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": ["body", "zip_code"],
      "msg": "String should match pattern '^361\\d{2}$'",
      "input": "99999"
    }
  ]
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (e.g., no plan exists for session) |
| 404 | Resource not found |
| 422 | Validation error (invalid request body or parameters) |
| 500 | Internal server error (corrupt data, unexpected failures) |
| 502 | Bad gateway (upstream service returned an error) |
| 503 | Service unavailable (dependency not configured or unreachable) |
| 504 | Gateway timeout (upstream service timed out) |

---

## Enumerations

### BarrierType

Used in the assessment request `barriers` object.

| Value | Description |
|-------|-------------|
| `credit` | Credit history barrier |
| `transportation` | Lacks reliable transportation |
| `childcare` | Needs childcare support |
| `housing` | Housing instability |
| `health` | Health-related barrier |
| `training` | Needs job training or certification |
| `criminal_record` | Criminal record barrier |

### EmploymentStatus

| Value | Description |
|-------|-------------|
| `unemployed` | Currently not employed |
| `underemployed` | Employed but seeking better work |
| `seeking_change` | Employed but looking to change fields |

### AvailableHours

| Value | Description |
|-------|-------------|
| `daytime` | Standard daytime hours |
| `evening` | Evening shift availability |
| `night` | Night shift availability |
| `flexible` | Open to any schedule |

### CrawlStatus

| Value | Description |
|-------|-------------|
| `starting` | Crawl job has been submitted |
| `running` | Crawl is in progress |
| `ready` | Crawl is complete, results available |
| `failed` | Crawl failed |

### BarrierSeverity

Determined by the number of barriers selected.

| Value | Condition |
|-------|-----------|
| `low` | 0-1 barriers |
| `medium` | 2 barriers |
| `high` | 3 or more barriers |
