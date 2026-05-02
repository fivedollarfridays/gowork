"""Route registry — collect all routers for app mounting."""

from app.barrier_intel.router import router as barrier_intel_router
from app.health import router as health_router
from app.routes.admin_flags import router as admin_flags_router
from app.routes.advisor_inbox import router as advisor_inbox_router
from app.routes.appointments import router as appointments_router
from app.routes.appointments_manage import router as appointments_manage_router
from app.routes.assessment import router as assessment_router
from app.routes.brightdata import router as brightdata_router
from app.routes.city import router as city_router
from app.routes.compliance import router as compliance_router
from app.routes.credit import router as credit_router
from app.routes.dashboard import router as dashboard_router
from app.routes.demo import router as demo_router
from app.routes.documents import router as documents_router
from app.routes.engagement import router as engagement_router
from app.routes.engagement_preview import router as engagement_preview_router
from app.routes.feedback import router as feedback_router
from app.routes.insights import router as insights_router
from app.routes.intelligence import router as intelligence_router
from app.routes.jobs import router as jobs_router
from app.routes.jobs_applications import router as jobs_applications_router
from app.routes.pathway import router as pathway_router
from app.routes.plan import router as plan_router
from app.routes.plan_haiku import router as plan_haiku_router
from app.routes.plan_intelligence import router as plan_intelligence_router
from app.routes.sendgrid_webhook import router as sendgrid_webhook_router
from app.routes.sequence import router as sequence_router
from app.routes.share import router as share_router
from app.routes.simulate import router as simulate_router
import app.routes.career_center as _career_center  # noqa: F401 — registers career-center route on plan_router

all_routers = [
    health_router,
    admin_flags_router,
    # appointments_manage (GET /api/appointments/manage) MUST be
    # registered before appointments_router; otherwise the
    # ``/{appointment_id}`` wildcard in appointments.py swallows the
    # /manage path.
    appointments_manage_router,
    appointments_router,
    assessment_router,
    plan_router,
    plan_haiku_router,
    share_router,
    sequence_router,
    simulate_router,
    credit_router,
    jobs_router,
    jobs_applications_router,
    brightdata_router,
    feedback_router,
    dashboard_router,
    barrier_intel_router,
    pathway_router,
    intelligence_router,
    plan_intelligence_router,
    city_router,
    insights_router,
    demo_router,
    documents_router,
    engagement_router,
    engagement_preview_router,
    sendgrid_webhook_router,
    compliance_router,
    advisor_inbox_router,
]
