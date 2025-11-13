"""
Special purpose router registration for the v1 API.
Contains emergency, master flows, FinOps, and other specialized routers.
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)


def register_special_routers(api_router: APIRouter):
    """Register special purpose routers (emergency, websocket, etc.)."""
    from app.api.v1.router_imports import routers_with_flags

    logger.info("--- Registering Special Routers ---")

    # Emergency System Control
    if routers_with_flags.get("EMERGENCY", (False, None))[0]:
        emergency_router = routers_with_flags["EMERGENCY"][1]
        api_router.include_router(emergency_router, prefix="/system")
        logger.info("✅ Emergency System Control router included")
    else:
        logger.warning("⚠️ Emergency System Control router not available")

    # Flow Health
    if routers_with_flags.get("FLOW_HEALTH", (False, None))[0]:
        flow_health_router = routers_with_flags["FLOW_HEALTH"][1]
        api_router.include_router(flow_health_router, prefix="/flows/health")
        logger.info("✅ Flow Health router included")
    else:
        logger.warning("⚠️ Flow Health router not available")

    # Agent Events for SSE
    if routers_with_flags.get("AGENT_EVENTS", (False, None))[0]:
        agent_events_router = routers_with_flags["AGENT_EVENTS"][1]
        api_router.include_router(agent_events_router, prefix="/agent-events")
        logger.info("✅ Agent Events router included")
    else:
        logger.warning("⚠️ Agent Events router not available")

    # Master Flows
    if routers_with_flags.get("MASTER_FLOWS", (False, None))[0]:
        master_flows_router = routers_with_flags["MASTER_FLOWS"][1]
        api_router.include_router(master_flows_router, prefix="/master-flows")
        logger.info("✅ Master Flows router included")
    else:
        logger.warning("⚠️ Master Flows router not available")

    # FinOps
    if routers_with_flags.get("FINOPS", (False, None))[0]:
        finops_router = routers_with_flags["FINOPS"][1]
        api_router.include_router(finops_router)
        logger.info("✅ FinOps router included")
    else:
        logger.warning("⚠️ FinOps router not available")

    # Canonical Applications
    if routers_with_flags.get("CANONICAL_APPLICATIONS", (False, None))[0]:
        canonical_applications_router = routers_with_flags["CANONICAL_APPLICATIONS"][1]
        api_router.include_router(
            canonical_applications_router, prefix="/canonical-applications"
        )
        logger.info(
            "✅ Canonical Applications router included at /canonical-applications"
        )
    else:
        logger.warning("⚠️ Canonical Applications router not available")

    # Applications (for Planning Flow wizard)
    if routers_with_flags.get("APPLICATIONS", (False, None))[0]:
        applications_router = routers_with_flags["APPLICATIONS"][1]
        api_router.include_router(applications_router)
        logger.info("✅ Applications router included at /api/v1/applications")
    else:
        logger.warning("⚠️ Applications router not available")

    # Wave Planning (for Plan Flow wizard)
    if routers_with_flags.get("WAVE_PLANNING", (False, None))[0]:
        wave_planning_router = routers_with_flags["WAVE_PLANNING"][1]
        api_router.include_router(wave_planning_router, prefix="/wave-planning")
        logger.info("✅ Wave Planning router included at /api/v1/wave-planning")
    else:
        logger.warning("⚠️ Wave Planning router not available")
