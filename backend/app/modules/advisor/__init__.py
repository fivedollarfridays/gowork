"""Advisor module — city-scoped queries backing the case-manager inbox (T12.31).

Hub re-exports the repository surface used by
:mod:`app.routes.advisor_inbox`. The city filter is enforced in
:mod:`app.modules.advisor.repository` — never in the route handler
alone (see ``docs/security/advisor-auth.md`` section 10, C2).
"""

from app.modules.advisor.repository import (
    AdvisorSessionDetail,
    AdvisorStalledSession,
    get_session_detail_for_city,
    list_stalled_sessions_for_city,
)

__all__ = [
    "AdvisorSessionDetail",
    "AdvisorStalledSession",
    "get_session_detail_for_city",
    "list_stalled_sessions_for_city",
]
