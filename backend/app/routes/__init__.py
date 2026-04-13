"""Route registry — collect all routers for app mounting."""

from app.barrier_intel.router import router as barrier_intel_router
from app.health import router as health_router
from app.routes.assessment import router as assessment_router
from app.routes.brightdata import router as brightdata_router
from app.routes.city import router as city_router
from app.routes.credit import router as credit_router
from app.routes.dashboard import router as dashboard_router
from app.routes.feedback import router as feedback_router
from app.routes.jobs import router as jobs_router
from app.routes.pathway import router as pathway_router
from app.routes.plan import router as plan_router
from app.routes.sequence import router as sequence_router
from app.routes.share import router as share_router
from app.routes.simulate import router as simulate_router
import app.routes.career_center as _career_center  # noqa: F401 — registers career-center route on plan_router

all_routers = [
    health_router,
    assessment_router,
    plan_router,
    share_router,
    sequence_router,
    simulate_router,
    credit_router,
    jobs_router,
    brightdata_router,
    feedback_router,
    dashboard_router,
    barrier_intel_router,
    pathway_router,
    city_router,
]
