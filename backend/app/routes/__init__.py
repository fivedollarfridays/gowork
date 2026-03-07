"""Route registry — collect all routers for app mounting."""

from app.health import router as health_router
from app.routes.assessment import router as assessment_router
from app.routes.brightdata import router as brightdata_router
from app.routes.credit import router as credit_router
from app.routes.feedback import router as feedback_router
from app.routes.jobs import router as jobs_router
from app.routes.plan import router as plan_router

all_routers = [
    health_router,
    assessment_router,
    plan_router,
    credit_router,
    jobs_router,
    brightdata_router,
    feedback_router,
]
