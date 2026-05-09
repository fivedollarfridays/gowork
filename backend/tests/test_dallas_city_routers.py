"""Dallas city-aware router validation -- T25.6 (Sprint 25 Wave 4).

The load-bearing "Dallas works" assertion. Every module that dispatches
on the active city via ``get_city_config()`` is exercised here with
``set_city_context('dallas')`` active, and the output is asserted to be
either:

(a) Texas-state-shared output identical to the FW (state="TX")
    output -- because the dispatch is keyed on ``city.state``, not on
    the city slug.  Dallas inherits the TX path for free.  Catching a
    regression here means a module accidentally started gating on the
    slug instead of the state -- a real plumbing bug.

(b) Routed through Dallas-specific data files in ``data/cities/dallas/``
    -- because the dispatch loads via ``city.data_dir`` /
    ``city.location`` / etc.  Catching a regression here means a Dallas
    data file isn't surfacing through to the runtime path.

Test design notes
=================

* Dispatch is checked via ``set_city_context('dallas')`` -- the same
  per-request context the assessment route sets in production, NOT a
  ``CITY=dallas`` env override.  This catches drift in either the
  context var path OR the env-var fallback.
* Each row carries a ``what_dallas_assertion_means`` docstring so a
  future failure points at the exact integration semantic that broke.
* Modules that load from ``city.data_dir`` (job_aggregator, honestjobs)
  are exercised through the actual file-loading path, not mocked --
  if the Dallas seed file went missing or moved, this test catches it.
* ``core.day_boundary`` is intentionally city-symmetric in dispatch
  (uses ``load_city_config(slug)`` for rollover_hour, no state branch).
  It is documented and skipped with rationale rather than asserted on
  -- the test exists to pin that ``rollover_hour`` is None/default
  for Dallas (no per-city override), which is the "no surprise" case.

Reference for the FW analog: ``test_fort_worth_integration.py``.
"""

from __future__ import annotations

from typing import Callable

import pytest

from app.cities.config import (
    clear_city_context,
    get_city_config,
    load_city_config,
    set_city_context,
)
from app.core.config import get_settings


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------


@pytest.fixture
def dallas_context():
    """Activate Dallas city context for the test, clear on teardown.

    Mirrors the per-request context the ``/api/assessment`` route sets
    after resolving the user's ZIP code.  Clears on teardown so a
    failure here doesn't leak into the next test (the autouse
    ``_pin_city_to_montgomery_for_tests`` env pin in conftest.py is
    independent of this contextvar).
    """
    # Defensive: ensure config caches see a fresh load for dallas.
    load_city_config.cache_clear()
    get_settings.cache_clear()
    set_city_context("dallas")
    try:
        yield load_city_config("dallas")
    finally:
        clear_city_context()
        load_city_config.cache_clear()
        get_settings.cache_clear()


# ---------------------------------------------------------------------
# Sanity: the context fixture actually activates Dallas
# ---------------------------------------------------------------------


class TestDallasContextActivation:
    """If these fail, every other assertion in this file is vacuous."""

    def test_get_city_config_returns_dallas(self, dallas_context):
        cfg = get_city_config()
        assert cfg.name == "Dallas"
        assert cfg.state == "TX"
        assert cfg.location == "Dallas, TX"

    def test_data_dir_points_at_dallas(self, dallas_context):
        cfg = get_city_config()
        assert cfg.data_dir == "data/cities/dallas"

    def test_job_adapters_includes_honestjobs(self, dallas_context):
        # T25.3 contract: Dallas adapters mirror FW exactly.
        cfg = get_city_config()
        assert cfg.job_adapters == ["twc", "usajobs", "honestjobs"]


# ---------------------------------------------------------------------
# Parametrized router dispatch -- the load-bearing matrix
# ---------------------------------------------------------------------


def _check_geo_router_uses_tx_data() -> None:
    """``geo_router`` must return FW (TX) coords + ZIPs for Dallas.

    What this asserts about Dallas behavior: ``city.state == "TX"`` is
    the dispatch key, so Dallas inherits Fort Worth's downtown coords
    and ZIP centroid table.  Until Dallas-specific ZIP centroids land
    (separate task), Dallas users get FW geo math -- accurate enough
    for the ~25-mile commute boost since DFW metro is one drive zone.
    """
    from app.modules.matching.geo_router import (
        get_downtown_coords,
        get_transit_hours,
        get_zip_centroids,
    )

    lat, lng = get_downtown_coords()
    # FW downtown ~= (32.7555, -97.3308) -- inside DFW box.
    assert 32.5 <= lat <= 33.0, f"Dallas geo_router downtown lat={lat} outside DFW"
    assert -97.6 <= lng <= -97.0, f"Dallas geo_router downtown lng={lng} outside DFW"

    centroids = get_zip_centroids()
    # FW ZIP table is shared with Dallas (state="TX" dispatch).
    assert "76102" in centroids, "TX-shared ZIP 76102 missing from Dallas geo_router"
    assert "36101" not in centroids, "Montgomery ZIP leaked into Dallas geo_router"

    start, end = get_transit_hours()
    # Sanity floor: transit hours are integers in [0, 24).
    assert isinstance(start, int) and isinstance(end, int)
    assert 0 <= start < 24 and 0 <= end <= 24


def _check_resource_router_uses_tx_data() -> None:
    """``resource_router`` returns TX-shared resources for Dallas.

    What this asserts about Dallas behavior: same state-keyed dispatch
    as geo_router.  Dallas inherits FW's career-center info, barrier
    actions, and certification DB.  A Dallas user opening their plan
    sees "Workforce Solutions for Tarrant County" until the Dallas-
    specific resource bundle ships -- this is a documented sprint-25
    inheritance, not a bug.
    """
    from app.modules.matching.resource_router import (
        get_barrier_actions,
        get_career_center,
        get_career_center_step,
        get_cert_db,
        get_resource_affinity,
    )

    cc = get_career_center()
    # TX dispatch returns the FW career center.  "Montgomery" leaking
    # in would mean the dispatch went down the AL branch.
    assert "Montgomery" not in cc.name, (
        f"AL career center leaked into Dallas: {cc.name!r}"
    )

    actions = get_barrier_actions()
    assert isinstance(actions, dict) and actions, "barrier actions empty for Dallas"

    step = get_career_center_step()
    assert "Montgomery" not in step, f"AL career-center step leaked: {step!r}"

    affinity = get_resource_affinity()
    assert isinstance(affinity, dict) and affinity

    cert_db = get_cert_db()
    assert isinstance(cert_db, dict) and cert_db


def _check_eligibility_dispatches_via_tx() -> None:
    """``DALLAS_ELIGIBILITY_RULES`` is reachable + has TX schema.

    What this asserts about Dallas behavior: the per-city eligibility
    dict is importable AND keys mirror the FW shape (so any caller
    doing ``RULES.get(name, ...)`` gets the same contract).  The
    state-gated dispatch lives at the call site; this test pins the
    artifact the call site reaches for.
    """
    from app.cities.dallas.eligibility import DALLAS_ELIGIBILITY_RULES
    from app.cities.fort_worth.eligibility import FORT_WORTH_ELIGIBILITY_RULES

    # Schema parity: every rule's "type" must be a known FW vocabulary
    # (open / income / enrollment / compound).  Drift here would mean
    # the eligibility caller can't dispatch on it.
    fw_types = {rule["type"] for rule in FORT_WORTH_ELIGIBILITY_RULES.values()}
    dallas_types = {rule["type"] for rule in DALLAS_ELIGIBILITY_RULES.values()}
    unknown = dallas_types - fw_types
    assert not unknown, (
        f"DALLAS_ELIGIBILITY_RULES uses unknown rule types: {unknown}"
    )

    # Required Dallas resources must be reachable via the dict key.
    for required in (
        "Workforce Solutions Greater Dallas",
        "DART",
        "Dallas College",
        "North Texas 211",
    ):
        assert required in DALLAS_ELIGIBILITY_RULES, (
            f"Dallas eligibility missing required resource: {required!r}"
        )


def _check_barrier_intel_prompts_use_tx() -> None:
    """Barrier-intel system prompt routes through TX context for Dallas.

    What this asserts about Dallas behavior: ``city.state == "TX"`` is
    again the dispatch key in ``barrier_intel/prompts.py``.  The system
    prompt for a Dallas user references the TX career center
    ("Workforce Solutions for Tarrant County") -- an inherited TX
    string until a Dallas-specific override ships.  The user-visible
    location string ("Dallas, TX") IS Dallas-correct (sourced from
    ``city.location``).
    """
    from app.barrier_intel.prompts import get_barrier_intel_system_prompt

    prompt = get_barrier_intel_system_prompt()
    # Location string MUST be Dallas-specific (sourced from city.location).
    assert "Dallas, TX" in prompt, (
        f"Dallas barrier-intel prompt missing 'Dallas, TX' location: "
        f"{prompt[:200]!r}"
    )
    # Career-center string is TX-shared -- confirms state branch hit.
    assert "Workforce Solutions for Tarrant County" in prompt, (
        "Dallas barrier-intel prompt did not route through TX branch"
    )
    # Should NEVER fall through to AL branch.
    assert "Alabama Career Center" not in prompt, (
        "Dallas barrier-intel prompt leaked AL career-center text"
    )
    assert "Montgomery" not in prompt, (
        "Dallas barrier-intel prompt leaked Montgomery text"
    )


def _check_barrier_intel_guardrails_use_tx() -> None:
    """Hallucination disclaimer routes through TX branch for Dallas.

    What this asserts about Dallas behavior: same state-keyed dispatch
    in ``barrier_intel/guardrails._get_hallucination_disclaimer``.
    Dallas inherits the FW disclaimer ("Workforce Solutions for
    Tarrant County at (817) 413-4400") -- a known TX-shared string.
    """
    from app.barrier_intel.guardrails import _get_hallucination_disclaimer

    disclaimer = _get_hallucination_disclaimer()
    # TX branch indicator -- Tarrant County phone number.
    assert "Tarrant County" in disclaimer, (
        f"Dallas guardrails did not route through TX branch: "
        f"{disclaimer[:200]!r}"
    )
    # AL branch sentinel that must NOT appear.
    assert "Montgomery" not in disclaimer
    assert "Alabama" not in disclaimer


def _check_brightdata_precrawl_uses_dallas_location() -> None:
    """Pre-crawl URLs target Dallas, TX (not FW or Montgomery).

    What this asserts about Dallas behavior: ``city.location`` is
    threaded through ``build_keyword_searches`` and ``build_search_urls``
    so BrightData crawls Dallas job sites.  This is a Dallas-SPECIFIC
    output path (NOT TX-shared) -- the location string differs between
    FW and Dallas.  A regression here would silently make Dallas users
    get FW listings.
    """
    from app.integrations.brightdata.precrawl import (
        build_keyword_searches,
        build_search_urls,
    )

    searches = build_keyword_searches()
    assert searches, "Dallas precrawl produced no keyword searches"
    for s in searches:
        assert s["location"] == "Dallas, TX", (
            f"Dallas precrawl search has wrong location: {s['location']!r}"
        )
        assert s["location"] != "Fort Worth, TX", (
            "Dallas precrawl leaked Fort Worth location"
        )
        assert s["location"] != "Montgomery, AL", (
            "Dallas precrawl leaked Montgomery location"
        )

    urls = build_search_urls()
    assert urls, "Dallas precrawl produced no search URLs"
    for url in urls:
        # Indeed search uses URL-encoded location ("Dallas%2C+TX").
        assert "Dallas" in url, f"Dallas URL missing 'Dallas': {url}"


def _check_job_aggregator_resolves_dallas_employers() -> None:
    """JobAggregator resolves Dallas employer + honestjobs seed paths.

    What this asserts about Dallas behavior: the active city's
    ``job_adapters`` config + ``data_dir`` resolve to real, parseable
    Dallas seed files on disk.  We don't run the full async aggregator
    (no DB session in this unit test) -- we verify the integration
    surface the aggregator depends on.

    The aggregator's behavior is: for each adapter in
    ``city_config.job_adapters``, dispatch to ``get_adapter(name)``
    and call ``fetch_jobs(session, query, location)`` with the city's
    location.  We pin the (adapter list, location, seed-file-existence)
    contract here.
    """
    from pathlib import Path

    from app.integrations.adapters.base import get_adapter

    cfg = get_city_config()
    # Aggregator iterates this list -- must be Dallas's adapter set.
    assert cfg.job_adapters == ["twc", "usajobs", "honestjobs"], (
        f"Dallas job_adapters drifted: {cfg.job_adapters}"
    )
    # Every adapter must be importable -- aggregator would 500 otherwise.
    for adapter_name in cfg.job_adapters:
        adapter = get_adapter(adapter_name)
        assert adapter is not None
        assert hasattr(adapter, "fetch_jobs"), (
            f"adapter {adapter_name!r} missing fetch_jobs"
        )

    # Dallas honestjobs seed file must be on disk for the honestjobs
    # adapter to surface listings (the aggregator's primary Dallas
    # data path -- twc + usajobs hit live APIs in production).
    project_root = Path(__file__).resolve().parent.parent.parent
    dallas_honestjobs = (
        project_root / "backend" / cfg.data_dir / "honestjobs_listings.json"
    )
    assert dallas_honestjobs.exists(), (
        f"Dallas honestjobs seed missing at {dallas_honestjobs} -- "
        f"aggregator would return zero Dallas-side honestjobs."
    )

    # Dallas employers seed (consumed by employer-aware matchers) must
    # also be on disk under city.data_dir.
    dallas_employers = project_root / cfg.data_dir / "employers.json"
    assert dallas_employers.exists(), (
        f"Dallas employers seed missing at {dallas_employers}"
    )


def _check_ai_client_fallback_uses_tx_branch() -> None:
    """``ai/client`` fallback narrative routes through TX branch.

    What this asserts about Dallas behavior: the city-aware fallback
    narrative (used when no API keys are configured -- the test
    environment) MUST select the TX branch via ``city.state == "TX"``,
    NOT raise ``ValueError`` for an unknown state.  A regression where
    a developer added a slug check (``city.name == "Fort Worth"``)
    would break Dallas here.
    """
    from app.ai.client import build_fallback_narrative

    # Minimal plan_data shape so the fallback builders don't choke.
    plan_data = {
        "barriers": [],
        "immediate_next_steps": [],
        "job_matches": [],
    }
    narrative = build_fallback_narrative(
        barriers=[],
        qualifications="",
        plan_data=plan_data,
        action_plan=None,
    )
    # Opening references the city name (sourced from city.name).
    assert "Dallas" in narrative.summary, (
        f"Dallas fallback summary missing city name: {narrative.summary!r}"
    )
    # TX-branch sentinel: Workforce Solutions for Tarrant County.
    assert "Workforce Solutions for Tarrant County" in narrative.summary, (
        "Dallas fallback summary did not route through TX branch"
    )
    # AL-branch sentinel must NOT appear.
    assert "Alabama" not in narrative.summary
    # Key actions must come from the TX-branch fallback list.
    assert narrative.key_actions, "Dallas fallback returned zero key actions"
    joined_actions = " ".join(narrative.key_actions)
    assert "Workforce Solutions" in joined_actions, (
        f"Dallas fallback actions did not route through TX branch: "
        f"{narrative.key_actions!r}"
    )


def _check_ai_providers_mock_uses_tx() -> None:
    """``MockProvider`` builds a TX-branched response for Dallas.

    What this asserts about Dallas behavior: the mock LLM provider
    (used in tests + offline degradation) selects the TX career-center
    string for Dallas, NOT the AL one.  Confirms the ``city.state``
    dispatch in ``ai.providers.MockProvider.build_response``.
    """
    from app.ai.providers import MockProvider

    response = MockProvider().build_response(user_prompt="anything")
    assert "Dallas" in response, (
        f"MockProvider response for Dallas missing city name: {response[:200]!r}"
    )
    assert "Workforce Solutions for Tarrant County" in response, (
        "MockProvider for Dallas did not route through TX branch"
    )
    assert "Alabama" not in response


def _check_ai_prompt_router_uses_tx() -> None:
    """``ai/prompt_router`` selects the TX system + user prompt for Dallas.

    What this asserts about Dallas behavior: ``get_system_prompt`` and
    ``get_user_prompt_template`` dispatch on ``city.state``.  Dallas
    gets the FW prompt template (until a Dallas-specific override
    lands in a future sprint -- the existing TX prompt mentions Fort
    Worth context).  This test pins that the dispatch went down the
    TX branch.
    """
    from app.ai.prompt_router import get_system_prompt, get_user_prompt_template

    sys_prompt = get_system_prompt()
    # TX branch sentinel -- Workforce Solutions for Tarrant County.
    assert "Workforce Solutions for Tarrant County" in sys_prompt, (
        "Dallas ai.prompt_router did not select TX system prompt"
    )
    # AL sentinel must NOT appear.
    assert "Alabama Career Center" not in sys_prompt

    user_template = get_user_prompt_template()
    # TX user template sentinel: "Fort Worth resident".  Inherited
    # by Dallas until a Dallas-specific template ships.  This is a
    # documented inheritance gap (xfail-worthy if a future sprint
    # adds a Dallas template; for now the TX inheritance IS the spec).
    assert "Fort Worth resident" in user_template, (
        "Dallas ai.prompt_router did not select TX user template "
        "(if a Dallas-specific template was added, update this test)"
    )


# Each row pairs an ID -> a check function.  Defined as a list of
# tuples so pytest.mark.parametrize stays readable in failure output.
_DALLAS_ROUTER_CHECKS: list[tuple[str, Callable[[], None]]] = [
    ("geo_router_dispatches_to_tx", _check_geo_router_uses_tx_data),
    ("resource_router_dispatches_to_tx", _check_resource_router_uses_tx_data),
    ("eligibility_dispatches_via_tx", _check_eligibility_dispatches_via_tx),
    ("barrier_intel_prompts_use_tx", _check_barrier_intel_prompts_use_tx),
    ("barrier_intel_guardrails_use_tx", _check_barrier_intel_guardrails_use_tx),
    ("brightdata_precrawl_uses_dallas_location",
        _check_brightdata_precrawl_uses_dallas_location),
    ("job_aggregator_resolves_dallas_employers",
        _check_job_aggregator_resolves_dallas_employers),
    ("ai_client_fallback_uses_tx", _check_ai_client_fallback_uses_tx_branch),
    ("ai_providers_mock_uses_tx", _check_ai_providers_mock_uses_tx),
    ("ai_prompt_router_uses_tx", _check_ai_prompt_router_uses_tx),
]


@pytest.mark.parametrize(
    "module_id, check_fn",
    _DALLAS_ROUTER_CHECKS,
    ids=[row[0] for row in _DALLAS_ROUTER_CHECKS],
)
def test_dallas_city_aware_module_dispatches_correctly(
    dallas_context, module_id: str, check_fn: Callable[[], None],
):
    """Each city-aware module returns Dallas-correct output.

    The check functions are kept as module-level callables so the
    parametrize ids match the module name and a failure points at the
    exact integration semantic that broke -- see each
    ``_check_*`` docstring for the "what does this assert about Dallas"
    contract.
    """
    check_fn()


# ---------------------------------------------------------------------
# Documented skips: city-symmetric modules that don't dispatch on city
# ---------------------------------------------------------------------


class TestDocumentedSymmetricModules:
    """Modules that load city config but don't dispatch on city/state.

    These are the "Dallas works for free" cases -- the dispatch is
    city-agnostic in design.  We pin the contract anyway so a future
    refactor that adds per-city branching here would surface the
    decision in this test (and trigger a design review).
    """

    def test_day_boundary_does_not_dispatch_on_state(self, dallas_context):
        """``core.day_boundary`` is city-symmetric in dispatch.

        The module loads the city config to read ``rollover_hour``
        (defaults to 4 when absent), but it doesn't branch on
        ``city.state``.  Dallas inherits the same default 4am rollover
        as FW + Montgomery because none of them set
        ``rollover_hour`` in their YAML.

        KNOWN INTEGRATION GAP: ``current_work_date("dallas")`` raises
        ``KeyError`` because ``TIMEZONE_BY_CITY`` in
        ``app.modules.common.temporal_types`` does NOT include
        ``"dallas"``.  T25.1 added the YAML + skeleton but did not
        wire Dallas into the timezone registry.  This test documents
        the gap; closing it is a one-line addition to the registry
        in a follow-up task.
        """
        from app.core.day_boundary import _resolve_rollover_hour

        # The slug-keyed rollover lookup works (no state branch, no
        # timezone needed for the rollover hour itself).
        hour = _resolve_rollover_hour("dallas")
        assert hour == 4, (
            f"Dallas rollover_hour drifted from default: {hour}"
        )
        # FW + Dallas must agree on rollover (both use the default
        # since neither sets ``rollover_hour`` in YAML).
        fw_hour = _resolve_rollover_hour("fort-worth")
        assert hour == fw_hour, (
            "Dallas rollover_hour diverged from FW -- both should "
            f"inherit default (Dallas={hour}, FW={fw_hour})"
        )
